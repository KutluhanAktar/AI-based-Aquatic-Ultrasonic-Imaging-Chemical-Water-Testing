<?php

# Get the current date and time.
$date = date("Y_m_d_H_i_s");

# Define the text file name of the received ultrasonic scan data.
$txt_file = "%s_%s__".$date;
$save_folder = "";

// If Arduino Nano ESP32 transfers the ultrasonic scan data with the selected sample type or the detected class (model results), modify the text file name dependently. 
if(isset($_GET["scan"]) && isset($_GET["type"]) && isset($_GET["class"])){
	$txt_file = sprintf($txt_file, $_GET["type"], $_GET["class"]);
	$save_folder = $_GET["type"];
}

// If Arduino Nano ESP32 transmits an ultrasonic scan sample or detection after running the neural network model, save the received information as a TXT file according to the provided variables — sample or detection.
if(!empty($_FILES["ultrasonic_scan"]['name'])){
	// Text File:
	$received_scan_properties = array(
	    "name" => $_FILES["ultrasonic_scan"]["name"],
	    "tmp_name" => $_FILES["ultrasonic_scan"]["tmp_name"],
		"size" => $_FILES["ultrasonic_scan"]["size"],
		"extension" => pathinfo($_FILES["ultrasonic_scan"]["name"], PATHINFO_EXTENSION)
	);
	
    // Check whether the uploaded file's extension is in the allowed file formats.
	$allowed_formats = array('jpg', 'png', 'bmp', 'txt');
	if(!in_array($received_scan_properties["extension"], $allowed_formats)){
		echo 'FILE => File Format Not Allowed!';
	}else{
		// Check whether the uploaded file size exceeds the 5 MB data limit.
		if($received_scan_properties["size"] > 5000000){
			echo "FILE => File size cannot exceed 5MB!";
		}else{
			// Save the uploaded file (TXT).
			move_uploaded_file($received_scan_properties["tmp_name"], "./".$save_folder."/".$txt_file.".".$received_scan_properties["extension"]);
			echo "FILE => Saved Successfully!";
		}
	}
}

?>