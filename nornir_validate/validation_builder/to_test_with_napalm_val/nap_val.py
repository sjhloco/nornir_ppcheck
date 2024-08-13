import napalm

# just to get the DICT returned by the "compliance_report"-Method in a readable manner on the screen
import pprint

pp = pprint.PrettyPrinter()

iosdriver = napalm.get_network_driver("ios")

DEVICE = "10.10.20.1"
USER = "test_user"
PASS = "L00K_pa$$w0rd_github!"
router = iosdriver(
    hostname=DEVICE,
    username=USER,
    password=PASS,
    optional_args={"port": 22, "dest_file_system": "bootflash:"},
)

router.open()
report = router.compliance_report("validate.yml")
router.close()

pp.pprint(report)
