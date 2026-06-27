#! ./.venv/Scripts/python.exe
# coding:utf-8

from PIL import Image, ImageSequence
import cv2
import os

import sys
import re
import importlib
import time

importlib.reload(sys)
import warnings

warnings.filterwarnings("ignore")

import xml.etree.ElementTree as ET
from xml.dom import minidom


'''

将一份mp4视频逐帧转换为DDS,并补齐对应的model,visual,mfm文件,以及完成seq文件的自动编写。
需事先完成一份model,viusal,mfm的编写以及一份基础geo,并在下方填写路径

'''
class Seq_conv:
    @staticmethod
    def prettify(elem):
        """
        将节点转换成字符串，并添加缩进。
        """
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    # model文件生成
    def model_generate(count,Path):

        file_name = Path.name + f"_{count}.model"    # 文件名
        output_path = os.path.join(Path.model_save_path, file_name)  # 输出路径
        visual_node = '\t' + Path.model_content_path + "/" + Path.name + f"_{count}.visual\t"  # 改动内容 visual节点

        # 读取样本文件
        tree_m = ET.parse(Path.model_path)
        root_m = tree_m.getroot()

        root_m.tag = file_name # 修改第一个tag
        root_m.find('visual').text = visual_node # 修改 visual节点

        # 生成新的model文件
        model_str = Seq_conv.prettify(root_m)
        # 去除版本声明
        model_str = '\n'.join([
            line for line in model_str.split('\n')
            if line.strip() != '<?xml version="1.0" ?>'
        ])
        # 去除空白行
        model_str = '\n'.join([
            line for line in model_str.split('\n')
            if line.strip() != ''
        ])
        f = open(output_path, 'w', encoding='utf-8')
        f.write(model_str)
        f.close()

        # print(visual_node)

    # visual文件生成
    def visual_generate(count, Path):
        file_name = Path.name+ f"_{count}.visual"    # 文件名
        output_path = os.path.join(Path.model_save_path, file_name)  # 输出路径
        mfm_node = '\t' + Path.model_content_path + "/" + Path.name + f"_{count}.mfm\t"    # 改动内容 renderSets -> renderSet -> material -> mfm节点
        # print(mfm_node)

        # 读取样本文件
        tree_v = ET.parse(Path.visual_path)
        root_v = tree_v.getroot()

        root_v.tag = file_name  # 修改第一个tag
        root_v.find('renderSets').find("renderSet").find("material").find("mfm").text = mfm_node  # 修改 mfm节点

        # 生成新的visual文件
        visual_str = Seq_conv.prettify(root_v)
        # 去除版本声明
        visual_str = '\n'.join([
            line for line in visual_str.split('\n')
            if line.strip() != '<?xml version="1.0" ?>'
        ])
        # 去除空白行
        visual_str = '\n'.join([
            line for line in visual_str.split('\n')
            if line.strip() != ''
        ])
        f = open(output_path, 'w', encoding='utf-8')
        f.write(visual_str)
        f.close()

    # mfm文件生成
    def mfm_generate(count,Path):
        file_name = Path.name + f"_{count}.mfm"  # 文件名
        output_path = os.path.join(Path.model_save_path, file_name)  # 输出路径
        diffuse_node = '\t' + Path.model_content_path + "/" + Path.name + f"_a_{count}.dds\t"  # 改动内容 property (内容为diffuseMap) -> Texture 节点
        # print(diffuse_node)

        # 读取样本文件
        tree_m = ET.parse(Path.mfm_path)
        root_m = tree_m.getroot()

        root_m.tag = file_name  # 修改第一个tag

        # 修改 diffuseMap(holographic.fx中为imageTexture)
        if "holographic" in root_m.find('fx').text:
            for elem in root_m.iter("property"):
                if "imageTexture" in elem.text:
                    elem.find("Texture").text = diffuse_node
        else:
            for elem in root_m.iter("property"):
                if "diffuseMap" in elem.text:
                    elem.find("Texture").text = diffuse_node

        # 生成新的mfm文件
        mfm_str = Seq_conv.prettify(root_m)
        # 去除版本声明
        mfm_str = '\n'.join([
            line for line in mfm_str.split('\n')
            if line.strip() != '<?xml version="1.0" ?>'
        ])
        # 去除空白行
        mfm_str = '\n'.join([
            line for line in mfm_str.split('\n')
            if line.strip() != ''
        ])
        f = open(output_path, 'w', encoding='utf-8')
        f.write(mfm_str)
        f.close()

    # geo文件复制
    def geo_generate(count, Path):
        file_name = Path.name + f"_{count}.geometry" # 文件名
        output_path = os.path.join(Path.model_save_path, file_name)  # 输出路径

        # 读取原geo
        f = open(Path.geo_path, 'rb')
        geo = f.read()
        # 写入新geo
        f = open(output_path, 'wb')
        f.write(geo)
        f.close()

    # seq文件生成
    def seq_generate(model_count,fps,frame_count, Path):
        file_name = Path.name + ".seq"  # 文件名
        output_path = os.path.join(Path.seq_save_path, file_name)  # 输出路径

        if not os.path.exists(Path.seq_save_path):  # 创建输出文件夹（如果不存在）
            os.makedirs(Path.seq_save_path)

        # 建立seq文件基础
        root_s = ET.Element(file_name)  # 创建需生成的seq文件的根节点

        # 生成duration节点
        duration = "{:.4f}".format(frame_count/fps)    # 计算seq播放时间
        n_duration = ET.SubElement(root_s, 'duration')
        n_duration.text = "\t" + str(duration) + "\t"

        # 生成root SQ节点
        n_sq_root = ET.SubElement(root_s, 'sequenceObject')
        sq_root_name = ET.SubElement(n_sq_root, 'name')
        sq_root_name.text = "\tRoot\t"
        sq_root_type = ET.SubElement(n_sq_root, 'type')
        sq_root_type.text = "\tmodel\t"
        sq_root_editorOnly = ET.SubElement(n_sq_root, 'editorOnly')
        sq_editorOnly_activated = ET.SubElement(sq_root_editorOnly, 'activated')
        sq_editorOnly_activated.text = "\ttrue\t"
        sq_editorOnly_solo = ET.SubElement(sq_root_editorOnly, 'solo')
        sq_editorOnly_solo.text = "\tfalse\t"
        sq_root_resource = ET.SubElement(n_sq_root, 'resource')
        sq_root_track = ET.SubElement(n_sq_root, 'track')

        # 生成帧 SQ节点
        count = 0
        while count <= (model_count-1):
            n_sq_frame = ET.SubElement(root_s, 'sequenceObject')
            sq_frame_name = ET.SubElement(n_sq_frame, 'name')
            sq_frame_name.text = "\t"+ Path.name + f"_{count}\t"
            sq_frame_type = ET.SubElement(n_sq_frame, 'type')
            sq_frame_type.text = "\tmodel\t"
            sq_frame_editorOnly = ET.SubElement(n_sq_frame, 'editorOnly')
            sq_editorOnly_activated = ET.SubElement(sq_frame_editorOnly, 'activated')
            sq_editorOnly_activated.text = "\ttrue\t"
            sq_editorOnly_solo = ET.SubElement(sq_frame_editorOnly, 'solo')
            sq_editorOnly_solo.text = "\tfalse\t"
            sq_frame_resource = ET.SubElement(n_sq_frame, 'resource')
            sq_frame_resource.text = "\t"+ Path.model_content_path + "/" + Path.name + f"_{count}.model\t"

            # position
            sq_frame_track = ET.SubElement(n_sq_frame, 'track')
            frame_track_name = ET.SubElement(sq_frame_track, 'name')
            frame_track_name.text = "\tposition\t"
            frame_track_type = ET.SubElement(sq_frame_track, 'type')
            frame_track_type.text = "\tvector3\t"
            frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
            track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
            track_frame_startTime.text = "\t0.0000\t"
            track_frame_value = ET.SubElement(frame_track_frame, 'value')
            track_frame_value.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_inTangent = ET.SubElement(frame_track_frame, 'inTangent')
            track_frame_inTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_outTangent = ET.SubElement(frame_track_frame, 'outTangent')
            track_frame_outTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_tangentMode = ET.SubElement(frame_track_frame, 'tangentMode')
            track_frame_tangentMode.text = "\t0.0000\t"

            # rotationEuler
            sq_frame_track = ET.SubElement(n_sq_frame, 'track')
            frame_track_name = ET.SubElement(sq_frame_track, 'name')
            frame_track_name.text = "\trotationEuler\t"
            frame_track_type = ET.SubElement(sq_frame_track, 'type')
            frame_track_type.text = "\tvector3\t"
            frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
            track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
            track_frame_startTime.text = "\t0.0000\t"
            track_frame_value = ET.SubElement(frame_track_frame, 'value')
            track_frame_value.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_inTangent = ET.SubElement(frame_track_frame, 'inTangent')
            track_frame_inTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_outTangent = ET.SubElement(frame_track_frame, 'outTangent')
            track_frame_outTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_tangentMode = ET.SubElement(frame_track_frame, 'tangentMode')
            track_frame_tangentMode.text = "\t0.0000\t"

            # scale
            sq_frame_track = ET.SubElement(n_sq_frame, 'track')
            frame_track_name = ET.SubElement(sq_frame_track, 'name')
            frame_track_name.text = "\tscale\t"
            frame_track_type = ET.SubElement(sq_frame_track, 'type')
            frame_track_type.text = "\tvector3\t"
            frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
            track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
            track_frame_startTime.text = "\t0.0000\t"
            track_frame_value = ET.SubElement(frame_track_frame, 'value')
            track_frame_value.text = "\t1.0000\t1.0000\t1.0000\t"
            track_frame_inTangent = ET.SubElement(frame_track_frame, 'inTangent')
            track_frame_inTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_outTangent = ET.SubElement(frame_track_frame, 'outTangent')
            track_frame_outTangent.text = "\t0.0000\t0.0000\t0.0000\t"
            track_frame_tangentMode = ET.SubElement(frame_track_frame, 'tangentMode')
            track_frame_tangentMode.text = "\t0.0000\t"

            # attach
            if count != 0:
                sq_frame_track = ET.SubElement(n_sq_frame, 'track')
                frame_track_name = ET.SubElement(sq_frame_track, 'name')
                frame_track_name.text = "\tattach\t"
                frame_track_type = ET.SubElement(sq_frame_track, 'type')
                frame_track_type.text = "\tattach\t"
                frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
                track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
                track_frame_startTime.text = "\t0.0000\t"
                track_frame_duration = ET.SubElement(frame_track_frame, 'duration')
                track_frame_duration.text = "\t" + str(duration) + "\t"
                track_frame_value = ET.SubElement(frame_track_frame, 'value')
                track_frame_value.text = "\t"+ Path.name + "_0\t"

            # visibility
            sq_frame_track = ET.SubElement(n_sq_frame, 'track')
            frame_track_name = ET.SubElement(sq_frame_track, 'name')
            frame_track_name.text = "\tvisibility\t"
            frame_track_type = ET.SubElement(sq_frame_track, 'type')
            frame_track_type.text = "\tbool\t"
            # 非第一帧需要在最初进行隐藏
            if count != 0:
                frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
                track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
                track_frame_startTime.text = "\t0.0000\t"
                track_frame_value = ET.SubElement(frame_track_frame, 'value')
                track_frame_value.text = "\tfalse\t"

            # 显示起始时间
            time = "{:.4f}".format(frame_count/fps/model_count*count)
            frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
            track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
            track_frame_startTime.text = "\t"+ str(time) +"\t"
            track_frame_value = ET.SubElement(frame_track_frame, 'value')
            track_frame_value.text = "\ttrue\t"

            # 显示结束时间
            time = "{:.4f}".format(frame_count/fps/model_count*(count+1))
            frame_track_frame = ET.SubElement(sq_frame_track, 'frame')
            track_frame_startTime = ET.SubElement(frame_track_frame, 'startTime')
            track_frame_startTime.text = "\t" + str(time) + "\t"
            track_frame_value = ET.SubElement(frame_track_frame, 'value')
            track_frame_value.text = "\tfalse\t"

            count += 1

        # 生成 events 节点
        n_sq_events = ET.SubElement(root_s, 'events')

        # 生成新的seq文件
        seq_str = Seq_conv.prettify(root_s)
        # 去除版本声明
        seq_str = '\n'.join([
            line for line in seq_str.split('\n')
            if line.strip() != '<?xml version="1.0" ?>'
        ])
        # 去除空白行
        seq_str = '\n'.join([
            line for line in seq_str.split('\n')
            if line.strip() != ''
        ])
        f = open(output_path, 'w', encoding='utf-8')
        f.write(seq_str)
        f.close()

    # 将视频逐帧转换为dds,并计算视频总长与每帧的时间(视频文件地址,输出文件夹,帧率间隔)
    def extract_frames(Path, path, output_folder, interval=3):
        cap = cv2.VideoCapture(path)  # 打开视频文件

        if not cap.isOpened():
            print("无法打开视频文件")
            return  # 检查视频是否成功打开

        fps = cap.get(cv2.CAP_PROP_FPS)  # 获取视频的帧率
        frame_interval = int(interval)
        if(frame_interval <= 0):
            frame_interval = 1

        if not os.path.exists(output_folder):  # 创建输出文件夹（如果不存在）
            os.makedirs(output_folder)
        if not os.path.exists("temp"):  # 创建临时存储文件夹（如果不存在）
            os.makedirs("temp")

        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = cap.read()  # 读取视频的下一帧
            if not ret:
                print("无法读取更多帧，可能是视频结束了。")
                break

            if frame_count % frame_interval == 0:  # 每隔指定的帧数保存一次图像
                output_path = os.path.join("temp", f"temp.png")
                if frame is not None:  # 检查帧是否为空
                    success = cv2.imwrite(output_path, frame)  # 保存图像
                    if success:
                        dds_image = Image.open("temp/temp.png")
                        # 生成dds图片
                        output = os.path.join(output_folder, Path.name + f"_a_{saved_count}.dds")
                        dds_image.save(output, pixel_format="DXT1")

                        # 生成对应模型文件
                        Seq_conv.model_generate(saved_count, Path)
                        Seq_conv.visual_generate(saved_count, Path)
                        Seq_conv.mfm_generate(saved_count, Path)
                        Seq_conv.geo_generate(saved_count, Path)
                        print(f"成功保存帧到 {output}")

                    saved_count += 1
                else:
                    print(f"在帧 {frame_count} 处读取的图像为空，跳过保存")

            frame_count += 1

        cap.release()
        Seq_conv.seq_generate(saved_count,fps,frame_count, Path)
        print(f"总帧数为 {frame_count} \n")
        # print("处理完成! \n")

    # 将gif逐帧转换为dds,并计算gif总长与每帧的时间(视频文件地址,输出文件夹,帧率间隔)
    def extract_frames_gif(Path, path, output_folder, interval=3):
        with Image.open(path) as gif:   # 打开gif文件
            fps = gif.info.get("duration",None)
            if fps is not None:
                fps = 1000/int(fps)
            else:
                fps = 20
            frame_interval = int(interval)
            if(frame_interval <= 0):
                frame_interval = 1

            if not os.path.exists(output_folder):  # 创建输出文件夹（如果不存在）
                os.makedirs(output_folder)
            if not os.path.exists("temp"):  # 创建临时存储文件夹（如果不存在）
                os.makedirs("temp")

            frame_count = 0
            saved_count = 0
            output_path = os.path.join("temp", f"temp.png")

            for frame in ImageSequence.Iterator(gif):
                if frame_count % frame_interval == 0:  # 每隔指定的帧数保存一次图像
                    if frame is not None:  # 检查帧是否为空
                        success =  frame.save(output_path)  # 保存图像

                        dds_image = Image.open("temp/temp.png")
                        if dds_image.mode == "P":
                            dds_image = dds_image.convert("RGBA")
                        # 生成dds图片
                        output = os.path.join(output_folder, Path.name + f"_a_{saved_count}.dds")
                        dds_image.save(output, pixel_format="DXT5")

                        # 生成对应模型文件
                        Seq_conv.model_generate(saved_count, Path)
                        Seq_conv.visual_generate(saved_count, Path)
                        Seq_conv.mfm_generate(saved_count, Path)
                        Seq_conv.geo_generate(saved_count, Path)
                        print(f"成功保存帧到 {output}")
                        saved_count += 1
                    else:
                        print(f"在帧 {frame_count} 处读取的图像为空，跳过保存")
                frame_count += 1

            Seq_conv.seq_generate(saved_count, fps, frame_count, Path)
            print(f"总帧数为 {frame_count} \n")
            # print("处理完成! \n")

    def seq_generater(Path):
        if (os.path.splitext(Path.video_path)[1] == '.gif') | (os.path.splitext(Path.video_path)[1] == '.apng'):
            # video_path,model_save_path,3
            print('alpha mode:')
            Seq_conv.extract_frames_gif(Path, Path.video_path, Path.model_save_path, Path.frame_inter)
        else:
            print('normal mode:')
            Seq_conv.extract_frames(Path, Path.video_path, Path.model_save_path, Path.frame_inter)

        return 0