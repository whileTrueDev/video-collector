# video to image (cropping)
# wsl
import cv2
import time
import os

user_dict = {
    'joni': '',
    'june': '',
    'luke': '',
    'mbaku': '',
    'martini': '',
    'robert': '',
    'scott': '',
    'woodie': '',
    'wony': '',
    'jiny': '',
    'simon': 'video_axiaxi_232068313'
}

class FrameGenerator():
    _file_name = None
    _vidcap = None
    _increase_width = 1
    duration = None


    def __init__(self, name):
        self._file_name = user_dict[name]
        
        self._vidcap = cv2.VideoCapture('../videos/' + self._file_name)
        fps = self._vidcap.get(cv2.CAP_PROP_FPS) 
        
        # 영상의 총 프레임 수를 get 클래스로 계산해 변수에 담음
        frame_count = self._vidcap.get(cv2.CAP_PROP_FRAME_COUNT)

        # 영상이 몇 초인지도 아래 나눗셈으로 계산이 가능. 변수에 담음
        self.duration = frame_count / fps
        print("당신의 영상은 총 {} 초짜리 입니다.".format(self.duration))
        

    def create_dir(self):
        try:
            if not os.path.exists('../save_frames/' + self._file_name):
                os.makedirs('../save_frames/' + self._file_name)
        except OSError:
            print ('Error: Creating directory. ')


    def get_frames(self, second = 0):
        self.create_dir()
        exit_flag = False
        success = True
        # read success!
        while success:

            # targe
            self._vidcap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
            success, image = self._vidcap.read()

            cv2.imshow('VideoCapture', image)
            
            while True:
                key = cv2.waitKey()  # key wait
                if key == 27:
                    exit_flag = True
                    break	# while문을 빠져나가기
                elif key == 91:
                    if second > 0:
                        second -= self._increase_width
                    break
                elif key == 93:
                    second += self._increase_width
                    break
                elif key == 115:
                    # frame save
                    cv2.imwrite("../save_frames/{}/frame_{}.jpg".format(self._file_name, second), image)
                        
                    second += self._increase_width
                    break
                else:
                    print('잘못된 입력입니다. [, ], s 중에 입력하세요.')


            if second > self.duration :
                break

            if not success or exit_flag :
                print('현재 종료시점은 {} 입니다. 다음 시점으로 입력하세요'.format(second))
                break

            if second % 100 == 0 :
                print('현재 {} 중에서 {} 만큼 진행하였습니다. '.format(int(self.duration), second)) 



if __name__ == '__main__':
    help_str = "당신의 영어이름을 소문자로 입력하세요: "
    name = None
    while True:
        name = input(help_str)
        if  name in user_dict.keys():
            break
        else: 
            help_str = '올바르지 않습니다. 당신의 영어이름을 소문자로 입력하세요: '
    
    fg = FrameGenerator(name)

    help_str = "영상 내에서 시작할 시점(초)를 입력하세요 (새로 시작은 0을 입력): "
    while True:
        second = input(help_str)
        second = int(second)
        if  second < fg.duration:
            break
        else: 
            help_str = '올바르지 않습니다. 영상 내에서 시작할 시점(초)를 입력하세요: '

    fg.get_frames(second)

