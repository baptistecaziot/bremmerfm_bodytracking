#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  9 18:32:44 2022

@author: bremmerlab
"""

import os, io, time, serial, threading
import cv2
import PySpin


data_path = './'
wait_time = 1

camera_fps = 24
tmax = 1200
n_images = camera_fps*tmax
image_height = 1080
image_width = 1440
# image_height = 321
# image_width = 216
bin_size = 1

# grab_timeout = int(1000*2/camera_fps)
stream_buffer_count = 200

# master_camera = '21190983'
# master_camera = '21187335'
master_camera = '21187339'
# master_camera = '21174907'
trigger_source_master = 'Line2'
trigger_source_slave = 'Line3'
exposure_time = int(4001) # microseconds
gain_value = 1 # in dB, 0-40;
gamma_value = 0.3 # 0.25-1

recording_time = time.strftime("%Y-%m-%d_%H-%M-%S")


print('Open Pyspin instance')
system = PySpin.System.GetInstance()
cameras = system.GetCameras()

# Thread frame writing
class ThreadWrite(threading.Thread):
    def __init__(self, image, writer):
        threading.Thread.__init__(self)
        self.image = image
        self.writer = writer

    def run(self):
        self.writer.Append(self.image)


# Capturing is also threaded, to increase performance
class ThreadCapture(threading.Thread):
    def __init__(self,camera,cn,vid_handle,pts_handle):
        threading.Thread.__init__(self)
        self.camera = camera
        self.cn = cn
        self.vid_handle = vid_handle
        self.pts_handle = pts_handle

    def run(self):
        
        timestamps = list()
        t0 = -1

        for im in range(n_images):
        # while 1:
            try:
                #  Get next frame
                # image_result = self.camera.GetNextImage()
                image_result = self.camera.GetNextImage(50)

                if (t0==-1):
                    t0 = image_result.GetTimeStamp()
                    t0_clock = time.time()
                    print('*** ACQUISITION STARTED ***')
                timestamps.append((image_result.GetTimeStamp()-t0)/1000000.0)
                # self.pts_handle.write('%d,%f\n' % (im,timestamps[im]))
                self.pts_handle.write(f'{im},{timestamps[im]},{(time.time()-t0_clock)*1000}\n')
                print('Camera %d, %s Frame %d, time %.2f' % (self.cn, self.camera.DeviceSerialNumber(), im,timestamps[im]/1000))
                
                # background = ThreadWrite(image_result, self.vid_handle)
                # background.start()
                self.vid_handle.Append(image_result)

                image_result.Release()
                
            except PySpin.SpinnakerException as ex:
                print('Error (577): %s' % ex)
                return 1
            except KeyboardInterrupt:
                print('Interrupted by user')
                return 0
            except Exception as ex:
                print(ex)
                return 1
        
        self.camera.EndAcquisition()
        
def configure_cam(camera, master):    
    try:
        nodemap = camera.GetNodeMap()
        try:
            camera.EndAcquisition()
            print(f"end aquisition {camera.DeviceSerialNumber()}")
            breakpoint()
        except:
            pass
        
        camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        
        print('Requested bin size: %i' % bin_size)
        if PySpin.IsWritable(camera.BinningHorizontal):
            camera.BinningHorizontal.SetValue(bin_size)
        if PySpin.IsWritable(camera.BinningVertical):
            camera.BinningVertical.SetValue(bin_size)
        print('Bin size: %ix%i.' % (camera.BinningHorizontal.GetValue(),camera.BinningVertical.GetValue()))
        
        resolution = [int(camera.SensorWidth.GetValue()/bin_size),int(camera.SensorHeight.GetValue()/bin_size)]
        
        if PySpin.IsWritable(camera.Width):
            camera.Width.SetValue(resolution[0])
        if PySpin.IsWritable(camera.Height):
            camera.Height.SetValue(resolution[1])
        print('Resolution: %ix%i.' % (camera.Width.GetValue(),camera.Height.GetValue()))
        # if not (camera.Width.GetValue==resolution[0] and camera.Height.GetValue()==resolution[1]):
        #     print("Wrong resolution")
        #     return 0

        
        if master:
            camera.AcquisitionFrameRateEnable.SetValue(True)
            camera.AcquisitionFrameRate.SetValue(camera_fps)
            camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            camera.LineSelector.SetValue(PySpin.LineSelector_Line2)
            camera.LineMode.SetValue(PySpin.LineMode_Output) 
            camera.LineSource.SetValue(PySpin.LineSource_ExposureActive)
        else:
            camera.AcquisitionFrameRateEnable.SetValue(False)
            # camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
            camera.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
            camera.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
            camera.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
            camera.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
            # camera.TriggerSelector.SetValue(PySpin.TriggerSelector_AcquisitionStart)
            camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
        
        
        # Retrieve Stream Parameters device nodemap
        camTLS = camera.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(camTLS.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('OldestFirst')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())
        
        # sNodeMap = camera.GetTLStreamNodeMap() 
        # camTLS.StreamBufferCountMode.SetValue(sNodeMap.GetNode('StreamBufferCountManual'))
        
        # # Set stream buffer Count Mode to manual
        # stream_buffer_count_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferCountMode'))
        # if not PySpin.IsAvailable(stream_buffer_count_mode) or not PySpin.IsWritable(stream_buffer_count_mode):
        #     print('Unable to set Buffer Count Mode (node retrieval). Aborting...\n')
        #     return False

        # stream_buffer_count_mode_manual = PySpin.CEnumEntryPtr(stream_buffer_count_mode.GetEntryByName('Manual'))
        # if not PySpin.IsAvailable(stream_buffer_count_mode_manual) or not PySpin.IsReadable(
        #         stream_buffer_count_mode_manual):
        #     print('Unable to set Buffer Count Mode entry (Entry retrieval). Aborting...\n')
        #     return False

        # stream_buffer_count_mode.SetIntValue(stream_buffer_count_mode_manual.GetValue())

        # # Retrieve and modify Stream Buffer Count
        # buffer_count = PySpin.CIntegerPtr(s_node_map.GetNode('StreamBufferCountManual'))
        # if not PySpin.IsAvailable(buffer_count) or not PySpin.IsWritable(buffer_count):
        #     print('Unable to set Buffer Count (Integer node retrieval). Aborting...\n')
        #     return False

        # # Set new buffer value
        # buffer_count.SetValue(stream_buffer_count)


        # Access trigger overlap info
        node_trigger_overlap = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerOverlap'))
        if not PySpin.IsAvailable(node_trigger_overlap) or not PySpin.IsWritable(node_trigger_overlap):
            print('Unable to set trigger overlap to "Read Out". Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        node_trigger_overlap_ro = node_trigger_overlap.GetEntryByName('ReadOut')
        
        if not PySpin.IsAvailable(node_trigger_overlap_ro) or not PySpin.IsReadable(
                node_trigger_overlap_ro):
            print('Unable to set trigger overlap (entry retrieval). Aborting...')
            return False

        # Retrieve integer value from enumeration
        trigger_overlap_ro = node_trigger_overlap_ro.GetValue()

        # Set trigger overlap using retrieved integer from enumeration
        node_trigger_overlap.SetIntValue(trigger_overlap_ro)

        # Access exposure auto info
        node_exposure_auto = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureAuto'))
        if not PySpin.IsAvailable(node_exposure_auto) or not PySpin.IsWritable(node_exposure_auto):
            print('Unable to get exposure auto. Aborting...')
            return False

        # Retrieve enumeration for trigger overlap Read Out
        node_exposure_auto_off = node_exposure_auto.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_exposure_auto_off) or not PySpin.IsReadable(
                node_exposure_auto_off):
            print('Unable to get exposure auto "Off" (entry retrieval). Aborting...')
            return False

        # Set exposure auto to off
        node_exposure_auto.SetIntValue(node_exposure_auto_off.GetValue())

        # Access exposure info
        node_exposure_time = PySpin.CFloatPtr(nodemap.GetNode('ExposureTime'))
        if not PySpin.IsAvailable(node_exposure_time) or not PySpin.IsWritable(node_exposure_time):
            print('Unable to get exposure time. Aborting...')
            return False

    except PySpin.SpinnakerException as ex:
        print('Error (237): %s' % ex)
        return False

    return True


def config_and_acquire(cam_list):
    threads = []
    # cam_list = [cam_list[1], cam_list[0]]
    for cn,camera in enumerate(cam_list):
        
        camera.Init()
        print('Setting camera %s' % camera.DeviceSerialNumber())
        
        # Configure camera
        if camera.DeviceSerialNumber()==master_camera:
            configure_cam(camera,1)
        else:
            configure_cam(camera,0)
            # configure_cam(camera,1)
        
    print("Initiated all cameras")
    time.sleep(1)
    
    
    vid_handles = []
    pts_handles = []
    print("Start acquiring")
    for cn,camera in enumerate(cam_list):
        print('camera', cn)
        # Open video file
        vid_filename = data_path+'headtracking_%s_%s'%(recording_time,camera.DeviceSerialNumber())
        
        # codec = 'mp4v'
        # fourcc = cv2.VideoWriter_fourcc(*codec)
        # vid_handle = cv2.VideoWriter(vid_filename,fourcc,camera_fps,(int(image_width/bin_size),int(image_height/bin_size)),1)
        
        # vid_handle = PySpin.SpinVideo()
        # vid_handles.append(vid_handle)
        # option = PySpin.AVIOption()
        # option.frameRate = camera_fps
        # vid_handle.Open(vid_filename, option)
        
        vid_handle = PySpin.SpinVideo()
        # option = PySpin.AVIption()
        option = PySpin.MJPGOption()
        option.frameRate = camera_fps
        option.height = int(image_height/bin_size)
        option.width = int(image_width/bin_size)
        vid_handle.Open(vid_filename, option)
        print('Opened video %s' % vid_filename)
        
        # Open timestamps file
        pts_filename = data_path+'headtracking_%s_%s.txt'%(recording_time,camera.DeviceSerialNumber())
        pts_handle = io.open(pts_filename, 'w')
        pts_handles.append(pts_handle)
        print('Opened file %s' % pts_filename)
        
        # Start acquisition thread
        camera.BeginAcquisition()
        img = camera.GetNextImage(5000)
        print(img.GetData())
        threads.append(ThreadCapture(camera,cn,vid_handle,pts_handle))
        # threads.append(NoThreadCapture(camera,cn,vid_handle,pts_handle))
        # threads[cn].run()
        threads[cn].start()
        

    print('*** WAITING FOR FIRST TRIGGER... ***\n')
    # wait_time = 0.5
    # print('Wait %d seconds' % wait_time)
    # time.sleep(wait_time)
    # msg = 'S'
    # sid.write(msg.encode()) 
        
    for tn, thread in enumerate(threads):
        pass
        thread.join()

    print('*** ALL THREAD CLOSED... ***\n')

    # msg = 'Q'
    # sid.write(msg.encode())
    # wait_time = 0.5

    # print('Wait %d seconds' % wait_time)
    # time.sleep(wait_time)

    for pts_handle in pts_handles:
        pts_handle.close()
    for vid_handle in vid_handles:
        vid_handle.Close()
    # vid_handle.release()
    
    for cn, camera in enumerate(cam_list):
        try:
            camera.EndAcquisition()
        except Exception as e:
            print(e)

    for cn, camera in enumerate(cam_list):
        print('deinit', cn)
        camera.DeInit()

def main():

    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    print('Number of cameras detected: %d' % num_cameras)
    
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        print('Not enough cameras! Goodbye.')
        return False
    else:
        config_and_acquire(cam_list)
   
    print('*** CLOSING... ***\n')

    # Clear cameras and release system instance
    cam_list.Clear()
    system.ReleaseInstance()

    print('DONE')
    time.sleep(.5)
    print('Goodbye :)')
    
    return 0

if __name__ == '__main__':
    main()


