import argparse
import errno
import logging
import os
from collections import OrderedDict
from contextlib import closing
from functools import partial
from itertools import chain

from streamlink import StreamError, Streamlink
from streamlink_cli.compat import is_win32
from streamlink_cli.console import ConsoleUserInputRequester
from streamlink_cli.constants import STREAM_SYNONYMS
from streamlink_cli.output import FileOutput, PlayerOutput
from streamlink_cli.utils import HTTPServer, progress

ACCEPTABLE_ERRNO = (errno.EPIPE, errno.EINVAL, errno.ECONNRESET)
try:
    ACCEPTABLE_ERRNO += (errno.WSAECONNABORTED,)
except AttributeError:
    pass  # Not windows
QUIET_OPTIONS = ("json", "stream_url", "subprocess_cmdline", "quiet")

args = console = streamlink = plugin = stream_fd = output = None

log = logging.getLogger("streamlink.cli")


def check_file_output(filename, force):
    """Checks if file already exists and ask the user if it should
    be overwritten if it does."""

    return FileOutput(filename)


# video streamming section
def create_output(plugin):
    """Decides where to write the stream.
    Depending on arguments it can be one of these:
     - The stdout pipe
     - A subprocess' stdin pipe
     - A named pipe that the subprocess reads from
     - A regular file
    """
    if arg_output:
        out = check_file_output(arg_output, False)
    else:
        title = arg_url
        log.info("Starting player: {0}".format(arg_player))
        print("Starting player: {0}".format(arg_player))
        out = PlayerOutput(arg_player)

    return out


def open_stream(stream):
    """Opens a stream and reads 8192 bytes from it.
    This is useful to check if a stream actually has data
    before opening the output.
    """
    global stream_fd

    # Attempts to open the stream
    try:
        stream_fd = stream.open()
    except StreamError as err:
        raise StreamError("Could not open stream: {0}".format(err))

    # Read 8192 bytes before proceeding to check for errors.
    # This is to avoid opening the output unnecessarily.
    try:
        log.debug("Pre-buffering 8192 bytes")
        prebuffer = stream_fd.read(8192)
    except OSError as err:
        stream_fd.close()
        raise StreamError("Failed to read data from stream: {0}".format(err))

    if not prebuffer:
        stream_fd.close()
        raise StreamError("No data returned from stream")

    return stream_fd, prebuffer

# afreecatv stream


def output_stream(plugin, stream):
    """Open stream, create output and finally write the stream to output."""
    global output

    success_open = False
    try:
        stream_fd, prebuffer = open_stream(stream)
        success_open = True
    except StreamError as err:
        log.error("Try {0}/{1}: Could not open stream {2} ({3})".format(
            1, 1, stream, err))

    output = create_output(plugin)
    try:
        output.open()
    except OSError as err:
        if isinstance(output, PlayerOutput):
            console.exit("Failed to start player: {0} ({1})",
                         arg_player, err)
        else:
            console.exit("Failed to open output: {0} ({1})",
                         arg_output, err)

    with closing(output):
        log.debug("Writing stream to output")
        read_stream(stream_fd, output, prebuffer)

    return True


def read_stream(stream, output, prebuffer, chunk_size=8192):
    """Reads data from stream and then writes it to the output."""
    is_player = isinstance(output, PlayerOutput)
    is_http = isinstance(output, HTTPServer)
    is_fifo = is_player and output.namedpipe

    stream_iterator = chain(
        [prebuffer],
        iter(partial(stream.read, chunk_size), b"")
    )

    # if show_progress:
    if arg_output:
        stream_iterator = progress(stream_iterator,
                                   prefix=os.path.basename(arg_output))

    try:
        for data in stream_iterator:
            # We need to check if the player process still exists when
            # using named pipes on Windows since the named pipe is not
            # automatically closed by the player.
            if is_win32 and is_fifo:
                output.player.poll()

                if output.player.returncode is not None:
                    log.info("Player closed")
                    break

            try:
                output.write(data)
            except OSError as err:
                if is_player and err.errno in ACCEPTABLE_ERRNO:
                    log.info("Player closed")
                elif is_http and err.errno in ACCEPTABLE_ERRNO:
                    log.info("HTTP connection closed")
                else:
                    console.exit("Error when writing to output: {0}, exiting", err)

                break
    except OSError as err:
        console.exit("Error when reading from stream: {0}, exiting", err)
    finally:
        stream.close()
        log.info("Stream ended")


def handle_stream(plugin, streams, stream_name):
    """Decides what to do with the selected stream.
    Depending on arguments it can be one of these:
     - Output internal command-line
     - Output JSON represenation
     - Continuously output the stream over HTTP
     - Output stream data to selected output
    """

    stream_name = resolve_stream_name(streams, stream_name)
    stream = streams[stream_name]

    for stream_name in [stream_name]:
        stream = streams[stream_name]
        stream_type = type(stream).shortname()
        success = output_stream(plugin, stream)

        if success:
            break


def resolve_stream_name(streams, stream_name):
    """Returns the real stream name of a synonym."""

    if stream_name in STREAM_SYNONYMS and stream_name in streams:
        for name, stream in streams.items():
            if stream is streams[stream_name] and name not in STREAM_SYNONYMS:
                return name

    return stream_name


def setup_streamlink():
    """Creates the Streamlink session."""
    global streamlink

    streamlink = Streamlink({"user-input-requester": ConsoleUserInputRequester(console)})


def setup_plugin_options(session, plugin):
    """Sets Streamlink plugin options."""
    pname = plugin.module
    required = OrderedDict({})

    for parg in plugin.arguments:
        if parg.options.get("help") == argparse.SUPPRESS:
            continue

        # value = getattr(args, parg.dest if parg.is_global else parg.namespace_dest(pname))
        session.set_plugin_option(pname, parg.dest, None)

        if not parg.is_global:
            if parg.required:
                required[parg.name] = parg
            # if the value is set, check to see if any of the required arguments are not set
            if parg.required:
                try:
                    for rparg in plugin.arguments.requires(parg.name):
                        required[rparg.name] = rparg
                except RuntimeError:
                    log.error(f"{pname} plugin has a configuration error and the arguments cannot be parsed")
                    break

    if required:
        for req in required.values():
            if not session.get_plugin_option(pname, req.dest):
                prompt = req.prompt or "Enter {0} {1}".format(pname, req.name)
                session.set_plugin_option(pname, req.dest,
                                          console.askpass(prompt + ": ")
                                          if req.sensitive else
                                          console.ask(prompt + ": "))


def get_video(argments):
    platform, user_id, broad_no, lock, broad_list = argments
    global arg_url
    global arg_player
    global arg_output
    error_code = 0
    url = None
    if platform == 'afreeca':
        url = 'http://play.afreecatv.com/' + user_id + '/' + broad_no
        stream_name = 'worst'
    else:
        url = 'https://www.twitch.tv/' + user_id
        stream_name = 'audio_only'

    file_name = './videos/video_{}_{}'.format(user_id, broad_no)
    arg_output = file_name
    arg_url = url
    arg_player = '/Applications/VLC.app/Contents/MacOS/VLC'
    try:
        setup_streamlink()

        # thread counts
        # streamlink.set_option("hls-segment-threads", 3)

        # download -> file save
        # streamlink.set_option("hls-segment-stream-data", True)

        # playlist reload counts
        streamlink.set_option("hls-playlist-reload-attempts", 1)

        # streamlink.set_option("hls-segment-timeout", args.hls_segment_timeout)
        streamlink.set_option("hls-timeout", 30)

        plugin = streamlink.resolve_url(arg_url)
        setup_plugin_options(streamlink, plugin)
        print(f"Found matching plugin {plugin.module} for URL {arg_url}")
        streams = plugin.streams()

        if stream_name in streams:
            lock.acquire()
            if not user_id in broad_list.keys():
                broad_list[user_id] = 1
            lock.release()
            handle_stream(plugin, streams, stream_name)
    except KeyboardInterrupt:
        error_code = 130
    finally:
        if stream_fd:
            try:
                print("Closing currently open stream...")
                log.info("Closing currently open stream...")
                stream_fd.close()
            except KeyboardInterrupt:
                error_code = 130
                # Close output
                if output:
                    output.close()
        ############ broad_list update section ############
        lock.acquire()
        if user_id in broad_list.keys():
            broad_list.pop(user_id)
        lock.release()