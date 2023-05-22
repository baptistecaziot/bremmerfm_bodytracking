import PySpin
import cameras_videos_v04 as c
from dataclasses import dataclass
from time import time

out_dir = 'out'
camera_fps = 24
    
master_camera = '21187339'
secondary1 = '21187335'
secondary2 = '21174907'
device_numbers = [master_camera, secondary1]

n_frames = 50
n_frames = 500
n_frames = 1
n_frames = 4320


class VideoHandle():
    def __init__(self, device_number):
        self.device_number = device_number
        self.option = PySpin.AVIOption()
        self.handle = PySpin.SpinVideo()
        fn = f'{out_dir}/{self.device_number}'
        self.handle.Open(fn, self.option)

    def append(self, frame):
        self.handle.Append(image)

    def close(self):
        self.handle.Close()


@dataclass
class ImageHandle():
    device_number: str

    def append(self, frame):
        frame.Save(f'{out_dir}/cam_{self.device_number}.png')

    def close(self):
        pass


def configure_cam(camera, master, mode=PySpin.AcquisitionMode_Continuous):
    
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
    Handle = ImageHandle
    acquisition_mode = PySpin.AcquisitionMode_SingleFrame
else:
    Handle = VideoHandle
    acquisition_mode = PySpin.AcquisitionMode_Continuous


system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
num_cameras = cam_list.GetSize()
print('Number of cameras detected: %d' % num_cameras)

for cn,camera in enumerate(cam_list):
    # camera.Width.SetValue(1440//2)
    # camera.Height.SetValue(1080//2)
    camera.Init()
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
    # cam = cams[device_number]
    # print('Set resolution from camera %s' % cam.DeviceSerialNumber())
    # cam.BeginAcquisition()
    # cam.EndAcquisition()
    # camera.Width.SetValue(1440//2)
    # camera.Height.SetValue(1080//2)

for device_number in device_numbers[::-1]:
    cam = cams[device_number]
    print('Aquire from camera %s' % cam.DeviceSerialNumber())
    # Start acquisition; note that secondary cameras have to be started first so acquisition of primary camera triggers secondary cameras.
    timestamps[device_number].append(str(time()))
    # cam.BeginAcquisition()
    # cam.EndAcquisition()
    # camera.Width.SetValue(1440//2)
    # camera.Height.SetValue(1080//2)
    cam.BeginAcquisition()

        
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
            timestamps[device_number].append(str(image.GetTimeStamp()/1000-t0_dict[device_number]))

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
