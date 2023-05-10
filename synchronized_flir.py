import PySpin
import cameras_videos_v04 as c

def configure_cam(camera, master):    
    
    if master:
        camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        camera.LineSelector.SetValue(PySpin.LineSelector_Line2)
    else:
        camera.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
        camera.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
        camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
    camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
    # camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
    
    
master_camera = '21187339'
secondary1 = '21187335'
secondary2 = '21174907'
device_numbers = [master_camera, secondary1]

system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
num_cameras = cam_list.GetSize()
print('Number of cameras detected: %d' % num_cameras)

for cn,camera in enumerate(cam_list):
    camera.Init()
    print('Setting camera %s' % camera.DeviceSerialNumber())
    if camera.DeviceSerialNumber()==master_camera:
        configure_cam(camera,1)
    else:
        configure_cam(camera,0)
print([cam.DeviceSerialNumber() for cam in cam_list])
cams = {cam.DeviceSerialNumber(): cam for cam in cam_list}

for device_number in device_numbers[::-1]:
    cam = cams[device_number]
    print('Aquire from camera %s' % cam.DeviceSerialNumber())
    # Start acquisition; note that secondary cameras have to be started first so acquisition of primary camera triggers secondary cameras.
    cam.BeginAcquisition()
    
images = {}
for device_number in device_numbers:
# for device_number in [secondary1, secondary2, master_camera]:
    cam = cams[device_number]
    # Acquire images
    print('GetNextImage from camera %s' % cam.DeviceSerialNumber())
    images[device_number] = cam.GetNextImage(1000)

for device_number in device_numbers:
    cam = cams[device_number]
    print('Save and end camera %s' % cam.DeviceSerialNumber())
    image = images[device_number]
    image.Save(f'cam_{device_number}.png')
    image.Release()
    cam.EndAcquisition()