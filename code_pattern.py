import numpy as np
import matplotlib.pyplot as plt
import math
from Encoding import _fmtEncode, _rsEncode


class code_pattern:
    def __init__(self, data):
        # 相关信息
        self.version = 6
        # H纠错等级的指示码，版本6的字节数，划分数据块数，每块数据数，每块纠错数
        self.relate_info = {'err_code': '10', 'total_bytes': 172, 'number_of_block': 4,
                            'per_block_data': 15, 'per_block_err': 28}
        # 对齐图案中心点位置
        self.align_pos = 34
        self.size = 21 + (self.version - 1) * 4
        # 0表示白，1表示黑，2表示未使用
        self.pattern = np.ones([self.size, self.size], dtype=int) * 2
        self.data = data
        # 格式：{'000':[[1,0,0,1]...[0,1,1,0],'001':...}
        self.masking_pattern = None
        self.masking_coding = None
        self.draw = False

        # 绘制相关图案
        if self.draw:
            plt.ion()
        self.get_position_pattern()
        self.get_position_round_pattern()
        self.get_alignment_pattern()
        self.get_timing_pattern()
        # 占用格式信息的位置，方便后续填入数据
        self.get_tmp_format_pattern()
        self.get_version_pattern()
        # 获取蒙版要填充的区域---在填充完其他区域后，填充数据前进行
        self.get_masking_pattern()
        self.fill_data()
        # 找到最适合的蒙版的编号
        self.find_best_masking_and_set()
        self.show()
        if self.draw:
            plt.pause(1000)

    def dynamic_draw(self):
        self.show()
        plt.pause(0.001)
        plt.clf()

    def show(self):
        pic = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if self.pattern[i][j] == 1:
                    pic[i][j] = 0
                elif self.pattern[i][j] == 0:
                    pic[i][j] = 255
                else:
                    pic[i][j] = 200
        plt.imshow(pic, cmap="gray")
        plt.axis('off')
        plt.show()

    def get_position_pattern(self):
        # 画好一个定位图案
        position_pattern = np.ones([7, 7], dtype=int)
        for i in range(1, 6):
            for j in range(1, 6):
                if i == 1 or i == 5:
                    position_pattern[i][j] = 0
                    continue
                if j == 1 or j == 5:
                    position_pattern[i][j] = 0
                    continue
        # 放在三个位置
        for i in range(0, 7):
            for j in range(0, 7):
                self.pattern[i][j] = position_pattern[i][j]
                self.pattern[i][j + self.size - 7] = position_pattern[i][j]
                self.pattern[i + self.size - 7][j] = position_pattern[i][j]
                if self.draw:
                    self.dynamic_draw()

    def get_position_round_pattern(self):
        for i in range(0, 8):
            self.pattern[i][7] = 0
            self.pattern[7][i] = 0
            self.pattern[i][self.size - 8] = 0
            self.pattern[self.size - 8][i] = 0
            self.pattern[i + self.size - 8][7] = 0
            self.pattern[7][i + self.size - 8] = 0
            if self.draw:
                self.dynamic_draw()

    def get_alignment_pattern(self):
        # 画好一个对齐图案
        alignment_pattern = np.ones([5, 5], dtype=int)
        for i in range(1, 4):
            for j in range(1, 4):
                if i == 1 or i == 3:
                    alignment_pattern[i][j] = 0
                    continue
                if j == 1 or j == 3:
                    alignment_pattern[i][j] = 0
                    continue
        # 只放置在一个位置
        for i in range(0, 5):
            for j in range(0, 5):
                self.pattern[i + self.align_pos - 2][j + self.align_pos - 2] = alignment_pattern[i][j]
                if self.draw:
                    self.dynamic_draw()

    def get_timing_pattern(self):
        fill_black = True
        for i in range(8, self.size - 7):
            if fill_black:
                self.pattern[6][i] = 1
                self.pattern[i][6] = 1
            else:
                self.pattern[6][i] = 0
                self.pattern[i][6] = 0
            fill_black = not fill_black
            if self.draw:
                self.dynamic_draw()

    def get_tmp_format_pattern(self):
        # 右上角0-7
        for i in range(0, 8):
            self.pattern[8][self.size - 1 - i] = 0
        # 左下角8-14
        for i in range(0, 7):
            self.pattern[self.size - 7 + i][8] = 0
        # 固定黑点
        self.pattern[self.size - 8][8] = 0
        # 左上角部分
        for i in range(0, 6):
            self.pattern[i][8] = 0
        for i in range(0, 6):
            self.pattern[8][5 - i] = 0
        # 位置是固定的
        self.pattern[7][8] = 0
        self.pattern[8][8] = 0
        self.pattern[8][7] = 0

    def get_version_pattern(self):
        # version7及以上才有
        pass

    def get_masking_area(self):
        masking_area = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if self.pattern[i][j] == 2:
                    masking_area[i][j] = 1
        return masking_area

    def get_masking_pattern(self):
        # 八个模板
        masking_array = {}
        masking_area = self.get_masking_area()
        ##########
        code = "000"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if (i + j) % 2 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "001"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if i % 2 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "010"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if j % 3 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "011"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if (i + j) % 3 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "100"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                # 这里有一点坑,不转为int会变成float+float
                if (int(i / 2) + int(j / 3)) % 2 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "101"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if ((i * j) % 2 + (i * j) % 3) == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "110"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if ((i * j) % 2 + (i * j) % 3) % 2 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking
        ##########
        code = "111"
        masking = np.zeros([self.size, self.size], dtype=int)
        for i in range(self.size):
            for j in range(self.size):
                if ((i * j) % 3 + (i + j) % 2) % 2 == 0:
                    masking[i][j] = masking_area[i][j]
        masking_array[code] = masking

        self.masking_pattern = masking_array

    def fill_data(self):
        # 右下角开始填充，先右后左，蛇形走位
        x = self.size - 1
        y = self.size - 1
        pos_right = True
        direct = 1  # 0向下  1向上
        index = 0
        data = _rsEncode(self.data, self.relate_info['per_block_data'],
                         self.relate_info['number_of_block'], self.relate_info['per_block_err'])
        remainder = 7
        while index < len(data) + remainder:
            if self.pattern[x][y] == 2:
                if index < len(data):
                    self.pattern[x][y] = int(data[index])
                # 把剩下7个空白补上--版本6剩下7个空白位置
                else:
                    self.pattern[x][y] = 0
                index = index + 1
            if pos_right:
                y = y - 1
            else:
                x = x + (-1) ** direct
                y = y + 1
            pos_right = not pos_right
            # 向上飞出天了
            if x < 0:
                direct = 0
                x = 0
                y = y - 2
                # 刚好碰到时序线,这个的位置固定y为6，要左移一格，
                if y == 6:
                    y = y - 1
            # 向下钻出地了
            if x > 40:
                direct = 1
                x = 40
                y = y - 2
            if self.draw:
                self.dynamic_draw()

    def find_best_masking_and_set(self):
        coding = ''
        score = 0
        for key in self.masking_pattern.keys():
            mask_score = self.get_mask_score(self.masking_pattern[key], key)
            if coding == '':
                coding = key
                score = mask_score
            else:
                if score > mask_score:
                    score = mask_score
                    coding = key
        self.masking_coding = coding
        # set
        # 可以针对去调整评价算法
        masking_pattern = self.masking_pattern[coding]
        # 执行异或操作
        for i in range(self.size):
            for j in range(self.size):
                self.pattern[i][j] = masking_pattern[i][j] ^ self.pattern[i][j]
                if self.draw:
                    self.dynamic_draw()
        self.get_format_pattern()

    def get_mask_score(self, masking_pattern, key):
        array = np.zeros([self.size, self.size], dtype=int)
        self.masking_coding = key
        self.get_format_pattern()
        # 执行异或操作
        for i in range(self.size):
            for j in range(self.size):
                array[i][j] = masking_pattern[i][j] ^ self.pattern[i][j]

        n1 = 0
        n2 = 0
        n3 = 0
        n4 = 0
        # 横竖存黑白相间次数的数组
        row_interval = []
        col_interval = []
        # 横竖连续5个以上颜色相同，分数：个数-2
        i = 0
        while i < self.size:
            j = 0
            interval = []
            while j < self.size:
                times = 0
                k = j
                while k < self.size and array[i][k] == array[i][j]:
                    k = k + 1
                    times = times + 1
                interval.append(times)
                if times >= 5:
                    n1 = n1 + times - 2
                j = k
            i = i + 1
            row_interval.append(interval)
        i = 0
        while i < self.size:
            j = 0
            interval = []
            while j < self.size:
                times = 0
                k = j
                while k < self.size and array[k][i] == array[j][i]:
                    k = k + 1
                    times = times + 1
                interval.append(times)
                if times >= 5:
                    n1 = n1 + times - 2
                j = k
            i = i + 1
            col_interval.append(interval)
        # 存在2X2颜色相同的块
        for i in range(self.size - 1):
            for j in range(self.size - 1):
                if array[i][j] == array[i + 1][j] and array[i][j] == array[i][j + 1]:
                    if array[i][j] == array[i + 1][j + 1]:
                        n2 = n2 + 3
        # 横竖出现1:1:3:1:1 的黑白黑白黑，且前面或后面有4个以上白
        for i in range(self.size):
            if array[i][0] == 1:
                first_dark = True
            else:
                first_dark = False
            # bug warning
            for j in range(1, len(row_interval[i])-5):
                if row_interval[i][j] == row_interval[i][j+1] and row_interval[i][j]*3 == row_interval[i][j+2]:
                    if row_interval[i][j] == row_interval[i][j+3] and row_interval[i][j] == row_interval[i][j+4]:
                        if row_interval[i][j-1] >= 4 and not first_dark:
                            n3 = n3 + 40
                            first_dark = not first_dark
                            continue
                        if row_interval[i][j+5] >= 4 and not first_dark:
                            n3 = n3 + 40
                            first_dark = not first_dark
                            continue
        for i in range(self.size):
            if array[0][i] == 1:
                first_dark = True
            else:
                first_dark = False
            # bug warning
            for j in range(1, len(col_interval[i])-5):
                if col_interval[i][j] == col_interval[i][j+1] and col_interval[i][j]*3 == col_interval[i][j+2]:
                    if col_interval[i][j] == col_interval[i][j+3] and col_interval[i][j] == col_interval[i][j+4]:
                        if col_interval[i][j-1] >= 4 and not first_dark:
                            n3 = n3 + 40
                            first_dark = not first_dark
                            continue
                        if col_interval[i][j+5] >= 4 and not first_dark:
                            n3 = n3 + 40
                            first_dark = not first_dark
                            continue
        # 黑色块的数量
        dark_num = array.sum()
        dark_rate = dark_num * 100 / (self.size * self.size)
        n4 = n4 + int(math.fabs(dark_rate - 50) / 5) * 10
        return n1 + n2 + n3 + n4

    def get_format_pattern(self):
        code = int(self.relate_info['err_code'] + self.masking_coding, 2)
        format_code = '{:015b}'.format(_fmtEncode(code))
        # 默认高位在前，反转一下
        format_code = format_code[::-1]
        # 右上角0-7
        for i in range(0, 8):
            self.pattern[8][self.size - 1 - i] = int(format_code[i])
        # 左下角8-14
        for i in range(0, 7):
            self.pattern[self.size - 7 + i][8] = int(format_code[i + 8])
        # 固定黑点
        self.pattern[self.size - 8][8] = 1
        # 左上角部分
        for i in range(0, 6):
            self.pattern[i][8] = int(format_code[i])
            self.pattern[8][5 - i] = int(format_code[9 + i])
        # 位置是固定的
        self.pattern[7][8] = int(format_code[6])
        self.pattern[8][8] = int(format_code[7])
        self.pattern[8][7] = int(format_code[8])
