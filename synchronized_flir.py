import PySpin
import cameras_videos_v04 as c
from dataclasses import dataclass
from time import time
from warnings import warn
from PIL import Image
import os

out_dir = 'out'
camera_fps = 60
    
master_camera = '21187339'
secondary1 = '21187335'
secondary2 = '21174907'
device_numbers = [master_camera, secondary1, secondary2]

n_frames = 5000
n_frames = 1000
n_frames = 1
n_frames = 50
n_frames = 4320
n_frames = 500


class VideoHandle():
    def __init__(self, device_number):
        self.device_number = device_number
        self.option = PySpin.AVIOption()
        self.option = PySpin.MJPGOption()
        self.handle = PySpin.SpinVideo()
        fn = f'{out_dir}/{self.device_number}'
        self.handle.Open(fn, self.option)

    def append(self, frame):
        self.handle.Append(image)

    def close(self):
        self.handle.Close()


class CompressedImagesHandle():
    def __init__(self, device_number):
        self.device_number = device_number
        os.makedirs(f'{out_dir}/jpeg_recording_{device_number}', exist_ok=True)
        cam = cams[device_number]
        self.width = cam.Width()
        self.height = cam.Height()
        self.i = 0
        self.handle = PySpin.SpinVideo()
    
    def append(self, frame):
        # frame.Convert(PySpin.PixelFormat_BayerRG8)
        # arr = frame.GetData().reshape(self.height, self.width)
        arr = frame.GetNDArray()
        im = Image.fromarray(arr) 
        im.save(f"{out_dir}/jpeg_recording_{self.device_number}/compressed_{self.device_number}_{self.i:05d}.jpeg")
        self.i += 1

    def close(self):
        pass


@dataclass
class ImageHandle():
    device_number: str

    def append(self, frame):
        frame.Save(f'{out_dir}/cam_{self.device_number}.png')

    def close(self):
        pass


def configure_cam(camera, master, mode=PySpin.AcquisitionMode_Continuous):
    
    # camera.BeginAcquisition()
    # camera.EndAcquisition()
    # camera.PixelFormat.SetValue(PySpin.PixelColorFilter_BayerRG)
    camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
    if master:
        # camera.LineSelector.SetValue(PySpin.LineSelector_Line1)
        # camera.LineSource.SetValue(PySpin.LineSource_ExposureActive)
        # camera.LineMode.SetValue(PySpin.LineMode_Output) 
        camera.LineSelector.SetValue(PySpin.LineSelector_Line2)
        # camera.LineMode.SetValue(PySpin.LineMode_Input) 
        # camera.V3_3Enable.SetValue(True)
        camera.AcquisitionFrameRate.SetValue(camera_fps)
        camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
    else:
        camera.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
        camera.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
        # camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
        camera.TriggerSelector.SetValue(PySpin.TriggerSelector_FrameStart)
    camera.AcquisitionMode.SetValue(mode)

if n_frames == 1:
    Handle = CompressedImagesHandle
    Handle = ImageHandle
    acquisition_mode = PySpin.AcquisitionMode_SingleFrame
else:
    Handle = VideoHandle
    Handle = CompressedImagesHandle
    acquisition_mode = PySpin.AcquisitionMode_Continuous


system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
num_cameras = cam_list.GetSize()
print('Number of cameras detected: %d' % num_cameras)

for cn,camera in enumerate(cam_list):
    camera.Init()
    # camera.Width.SetValue(1440//2)
    # camera.Height.SetValue(1080//2)
    device_number = camera.DeviceSerialNumber()
    if device_number not in device_numbers:
        print(f"Skip {device_number}")
        continue
    print('Setting camera %s' % device_number)
    if device_number==master_camera:
        configure_cam(camera,1, acquisition_mode)
    else:
        configure_cam(camera,0, acquisition_mode)

print([cam.DeviceSerialNumber() for cam in cam_list])
cams = {cam.DeviceSerialNumber(): cam for cam in cam_list}

timestamps = {device: [] for device in device_numbers}
t0_dict = {}

# for device_number in device_numbers[::-1]:
#     cam = cams[device_number]
#     cam.BeginAcquisition()
#     cam.EndAcquisition()

for device_number in device_numbers[::-1]:
    cam = cams[device_number]
    print('Aquire from camera %s' % cam.DeviceSerialNumber())
    # Start acquisition; note that secondary cameras have to be started first so acquisition of primary camera triggers secondary cameras.
    timestamps[device_number].append(str(time()))
    cam.BeginAcquisition()
    # cam.EndAcquisition()
#     camera.Width.SetValue(1440//2)
#     camera.Height.SetValue(1080//2)
        
handle = {key: Handle(key) for key in device_numbers}
    
for frame_n in range(n_frames):
    for device_number in device_numbers:
        cam = cams[device_number]
        print(f'{frame_n:03d}: GetNextImage from camera {cam.DeviceSerialNumber()}')
        if frame_n == 0:
            timestamps[device_number].append(str(time()))
        image = cam.GetNextImage()
        if frame_n == 0:
            timestamps[device_number].append(str(time()))
            t0 = image.GetTimeStamp()/1000
            timestamps[device_number].append(str(t0))
            t0_dict[device_number] = t0
        else:
            t = image.GetTimeStamp()/1000-t0_dict[device_number]
            timestamps[device_number].append(str(t))
            if device_number == device_numbers[-1]:
                t_diff = abs(t - float(timestamps[device_numbers[0]][-1]))
                if t_diff > 17000:
                    warn(f"timestamp diff = {t_diff}")
                    

        cam = cams[device_number]
        handle[device_number].append(image)
        image.Release()

# for device_number in device_numbers:
#     cam.EndAcquisition()
with open(f'{out_dir}/timing.txt', 'w') as fh:
    fh.write(', '.join(timestamps.keys())+'\n')
    fh.writelines([", ".join(t)+'\n' for t in zip(*timestamps.values())])

for key, h in handle.items():
    print(f'Save and end camera {key}')
    h.close()
