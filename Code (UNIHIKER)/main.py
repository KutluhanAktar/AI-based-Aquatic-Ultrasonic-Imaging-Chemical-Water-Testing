# AI-based Aquatic Ultrasonic Imaging & Chemical Water Testing
#
# UNIHIKER
#
# By Kutluhan Aktar
#
# Identify noxious air bubbles lurking in the substrate w/ ultrasonic scans
# and assess water pollution based on chemical tests simultaneously.
# 
#
# For more information:
# https://www.hackster.io/kutluhan-aktar


from _class import aquarium_func
from threading import Thread


# Define the aquarium object.
aquarium = aquarium_func("model/ai-based-aquatic-chemical-water-quality-testing-linux-aarch64.eim")

# Define and initialize threads.
Thread(target=aquarium.camera_feed).start()
Thread(target=aquarium.board_configuration).start()

# Show the user interface (GUI) designed with the built-in UNIHIKER modules.
aquarium.create_user_interface()