import PySpin
import cameras_videos_v04 as c
from dataclasses import dataclass


class VideoHandle():
    def __init__(self, device_number):
        self.device_number = device_number
        self.option = PySpin.AVIOption()
        self.handle = PySpin.SpinVideo()
        fn = f'out/{self.device_number}'
        self.handle.Open(fn, self.option)

    def append(self, frame):
        self.handle.Append(image)

    def close(self):
        self.handle.Close()


@dataclass
class ImageHandle():
    device_number: str

    def append(self, frame):
        frame.Save(f'cam_{self.device_number}.png')

    def close(self):
        pass


def configure_cam(camera, master, mode=PySpin.AcquisitionMode_Continuous):
    
    if master:
        camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        camera.LineSelector.SetValue(PySpin.LineSelector_Line2)
    else:
        camera.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
        camera.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
        camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
    camera.AcquisitionMode.SetValue(mode)
    
    
master_camera = '21187339'
secondary1 = '21187335'
secondary2 = '21174907'
device_numbers = [master_camera, secondary1, secondary2]

n_frames = 500

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
    camera.Init()
    print('Setting camera %s' % camera.DeviceSerialNumber())
    if camera.DeviceSerialNumber()==master_camera:
        configure_cam(camera,1, acquisition_mode)
    else:
        configure_cam(camera,0, acquisition_mode)

print([cam.DeviceSerialNumber() for cam in cam_list])
cams = {cam.DeviceSerialNumber(): cam for cam in cam_list}

for device_number in device_numbers[::-1]:
    cam = cams[device_number]
    print('Aquire from camera %s' % cam.DeviceSerialNumber())
    # Start acquisition; note that secondary cameras have to be started first so acquisition of primary camera triggers secondary cameras.
    cam.BeginAcquisition()

        
handle = {key: Handle(key) for key in device_numbers}
    
time = {device: [] for device in cams}
for frame_n in range(n_frames):
    for device_number in device_numbers:
        cam = cams[device_number]
        print('GetNextImage from camera %s' % cam.DeviceSerialNumber())
        image = cam.GetNextImage()
        time[device_number].append(str(image.GetTimeStamp()/1000))

        cam = cams[device_number]
        handle[device_number].append(image)
        image.Release()

# for device_number in device_numbers:
#     cam.EndAcquisition()
with open('timing.txt', 'w') as fh:
    fh.writelines([", ".join(t)+'\n' for t in zip(*time.values())])

for key, h in handle.items():
    print(f'Save and end camera {key}')
    h.close()
