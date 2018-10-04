from harvesters.core import Harvester

h = Harvester()

h.add_cti_file('/usr/local/lib/baumer/libbgapi2_gige.cti')

h.update_device_info_list()

h.device_info_list

iam = h.create_image_acquisition_manager(serial_number='QG0170070016')