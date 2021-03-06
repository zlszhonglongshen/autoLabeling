#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time        :2020/11/3 14:00
# @Author      :weiz
# @ProjectName :autoLabeling
# @File        :dataLabeling.py
# @Description :数据标注文件
import os
import codecs
import cv2

import yoloMain


def vocXMLFormat(filePath, imgName, imgW, imgH, objNames, locs, depth=3, truncated=0, difficult=0):
    """
    生成xml数据文件;eg:
        vocXMLFormat("0000.xml", "0001.png", 608, 608, ["person", "TV"], [[24, 32, 156, 145], [124, 76, 472, 384]])
    :param filePath: 生成xml所保存文件的路径
    :param imgName: xml文件标注图片的名字
    :param imgW: 图片的宽
    :param imgH: 图片的高
    :param objNames: 图片包含的目标，格式：["目标1","目标2"...]
    :param locs: 图片包含目标的坐标，格式：[[x,y,w,h],[x,y,w,h]...]
    :param depth: 图片的深度，默认是3
    :param truncated: 是否被截断（0表示完整）
    :param difficult: 目标是否难以识别（0表示容易识别）
    :return:
    """
    if (objNames == None) or (locs == None):
        print("The objNames or locs is None!!!")
        return
    with codecs.open(filePath, 'w', 'utf-8') as xml:
        xml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml.write('<annotation>\n')
        xml.write('\t<folder>' + 'voc format' + '</folder>\n')
        xml.write('\t<filename>' + imgName + '</filename>\n')
        xml.write('\t<path>' + imgName + '</path>\n')
        xml.write('\t<source>\n')
        xml.write('\t\t<database>weiz</database>\n')
        xml.write('\t</source>\n')
        xml.write('\t<size>\n')
        xml.write('\t\t<width>' + str(imgW) + '</width>\n')
        xml.write('\t\t<height>' + str(imgH) + '</height>\n')
        xml.write('\t\t<depth>' + str(depth) + '</depth>\n')
        xml.write('\t</size>\n')
        xml.write('\t<segmented>0</segmented>\n')

        for ind, name in enumerate(objNames):
            xml.write('\t<object>\n')
            xml.write('\t\t<name>' + name + '</name>\n')
            xml.write('\t\t<pose>Unspecified</pose>\n')
            xml.write('\t\t<truncated>' + str(truncated) + '</truncated>\n')
            xml.write('\t\t<difficult>' + str(difficult) + '</difficult>\n')
            xml.write('\t\t<bndbox>\n')
            xml.write('\t\t\t<xmin>' + str(locs[ind][0]) + '</xmin>\n')
            xml.write('\t\t\t<ymin>' + str(locs[ind][1]) + '</ymin>\n')
            xml.write('\t\t\t<xmax>' + str(locs[ind][0] + locs[ind][2]) + '</xmax>\n')
            xml.write('\t\t\t<ymax>' + str(locs[ind][1] + locs[ind][3]) + '</ymax>\n')
            xml.write('\t\t</bndbox>\n')
            xml.write('\t</object>\n')

        xml.write('</annotation>')
    xml.close()
    print("The {} accomplish!".format(filePath))


def autoLabeling(yoloModel, modelSign, savePath, img, imgName=None, extraName=None, depth=3, truncated=0, difficult=0):
    """
    生成标注图片img的xml文件
    :param yoloModel: yolov3或者yolov4
    :param modelSign: 模型标识位，3表示yolov3,4表示yolov4
    :param savePath: 保存路径
    :param img: 图片
    :param imgName: 图片的名字
    :param extraName: 附加额外的名字：默认是从000001.png开始命名图片；如果该参数为hsh，则命名从hsh_000001.png开始
    :param depth: 图片的深度
    :param truncated: 是否被截断（0表示完整）
    :param difficult: 目标是否难以识别（0表示容易识别）
    :return:
    """
    global savePathFolderNum
    if savePathFolderNum == -1:
        try:
            savePathFolderNum = 0
            fileList = os.listdir(savePath)
            for file in fileList:        # 统计png文件的个数
                if "png" in os.path.splitext(file)[-1]:
                    savePathFolderNum = savePathFolderNum + 1
        except FileNotFoundError:
            os.mkdir(savePath)
            savePathFolderNum = 0
    if imgName == None:                  # 确定保存图片的名字
        if extraName != None:
            imgName = extraName + '_' + "{:0>6d}".format(savePathFolderNum)
        else:
            imgName = "{:0>6d}".format(savePathFolderNum)
    else:
        if extraName != None:
            imgName = extraName + '_' + imgName

    imgPath = os.path.join(savePath, imgName + ".png")
    xmlPath = os.path.join(savePath, imgName + ".xml")

    locs, labels = getLabelInfo(yoloModel, modelSign, img)
    if len(labels) > 0:
        savePathFolderNum = savePathFolderNum + 1
        vocXMLFormat(xmlPath, imgName + ".png", img.shape[1], img.shape[0], labels, locs, depth, truncated, difficult)
        cv2.imwrite(imgPath, img)

    return locs, labels


def getLabelInfo(yoloModel, modelSign, img):
    """
    实现图片的检测，并返回标注信息,eg:
        labels = ["person", "TV"]
        locs = [[24, 32, 156, 145], [124, 76, 472, 384]]
    :param yoloModel:
    :param modelSign:
    :param img:
    :return: 返回labels和locs，格式：["目标1","目标2"...]和[[x,y,w,h],[x,y,w,h]...]
    """
    if modelSign == 3:
        boxes, labels, confs, timeLabel = yoloMain.runningYolov3(yoloModel, img)
    elif modelSign == 4:
        boxes, labels, confs, timeLabel = yoloMain.runningYolov4(yoloModel, img)
    else:
        print("3:yolov3   4:yolov4")
        exit()

    locs = []
    if boxes == []:
        return locs, labels
    for x1, y1, x2, y2 in boxes:
        w = x2 - x1
        h = y2 - y1
        locs.append([x1, y1, w, h])

    return locs, labels


def showAnnotions(image, locs, labels):
    """
    显示标注
    :param locs:
    :param labels:
    :return:
    """
    for ind, (x, y, w, h) in enumerate(locs):
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(image, labels[ind], (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)


def videoAnnotation(videoPath, savePath, gap=10, yoloModels=3):
    """
    自动标注视频数据
    :param videoPath: 视频的路径
    :param savePath: 标注后保存的路径
    :param gap: 每多少帧才标注
    :param yoloModels: 使用yolov3或者yolov4模型，默认使用yolov3
    :return:
    """
    if yoloModels != 4:   # 使用yolov3
        yoloModels = yoloMain.getYolov3()
        modelSign = 3
    else:                 # 使用yolov4
        yoloModels = yoloMain.getYolov4()
        modelSign = 4
    cap = cv2.VideoCapture(videoPath)
    frameNum = 0
    videoName = os.path.splitext(os.path.basename(videPath))[0]
    while True:
        ok, img = cap.read()
        frameNum = frameNum + 1
        if not ok:
            break
        if frameNum % gap != 0:
            continue

        locs, labels = autoLabeling(yoloModels, modelSign, savePath, img, extraName=videoName)
        showAnnotions(img, locs, labels)

        cv2.imshow('video', img)
        if cv2.waitKey(1) & 0xFF == 27:
            cap.release()  # 关闭摄像头
            break

    cv2.destroyAllWindows()


def imagesAnnotation(imagesPath, savePath, yoloModels=3):
    """
    图片自动标注
    :param imagesPath:
    :param savePath:
    :param yoloModels:
    :return:
    """
    if yoloModels != 4:   # 使用yolov3
        yoloModels = yoloMain.getYolov3()
        modelSign = 3
    else:                 # 使用yolov4
        yoloModels = yoloMain.getYolov4()
        modelSign = 4

    imagesList = os.listdir(imagesPath)
    for imageName in imagesList:
        imagePath = os.path.join(imagesPath, imageName)
        image = cv2.imread(imagePath)

        locs, labels = autoLabeling(yoloModels, modelSign, savePath, image, os.path.splitext(imageName)[0])
        showAnnotions(image, locs, labels)

        cv2.imshow("image", image)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()


videPath = "./videos/004.avi"
imagesPath = "./srcImages"            # 待标注的图片
savePath = "C:/Users/weiz/Desktop/annotions"        # 该文件可以不存在，会自动创建
savePathFolderNum = -1                              # 所存路径文件的个数，-1表示还没有读取
yoloMoels = 3                                       # 3表示使用yolov3模型标注，4表示使用yolov4标注
if __name__ == "__main__":
    #videoAnnotation(videPath, savePath, 10, yoloMoels)

    imagesAnnotation(imagesPath, savePath, yoloMoels)