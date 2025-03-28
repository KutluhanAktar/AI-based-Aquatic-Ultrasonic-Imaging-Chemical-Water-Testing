<?php

// Obtain the data items for each ultrasonic scan stored in the sample folder as text files.
function read_scans(){
	$information = [];
	// Get all text file paths under the sample folder.
	$files = glob("./sample/*.txt");
	// Read each text file to obtain the ultrasonic scan information — data items.
	foreach($files as $scan){
		$line = [];
		// Derive the provided air bubble label from the given text file name.
		$label = explode("_", $scan)[1];
		array_push($line, $label);
		// Read the ultrasonic scan information.
		$record = fopen($scan, "r"); 
		$data_items = fread($record, filesize($scan));
		// Remove the redundant comma from the data record (scan).
		$data_items = substr($data_items, 0, -1);
		// Append the retrieved data items.
		$data_items = explode(",", $data_items);
		$line = array_merge($line, $data_items);
        array_push($information, $line);
        // Close the text file.
		fclose($record);
	}
	// Return the fetched data items.
	return $information;
}

// Generate a CSV file from the data records (ultrasonic scan information sent by Nano ESP32) stored in the sample folder.
function create_CSV(){
	// Obtain the generated data items array from ultrasonic scans — data records.
	$information = read_scans();
	// Create the scan_data_items.csv file.
	$filename = "scan_data_items.csv";
	$fp = fopen($filename, 'w');
	// Create and add the header to the CSV file.
	$header = [];
	array_push($header, "air_bubble_label");
	for($i=0;$i<400;$i++){ array_push($header, "p_".strval($i)); }
	fputcsv($fp, $header);
	// Append the retrieved data items as rows for each ultrasonic scan to the CSV file.
	foreach($information as $row){
		fputcsv($fp, $row);
	}
	// Close the CSV file.
	fclose($fp);
}

// Obtain the latest data record (ultrasonic scan data points) with the neural network model detection result stored in the detection folder.
function get_latest_detection($folder){
	$scan = scandir($folder, 1);
	// Label (model result).
	$model_result = explode("_", $scan[0])[1];
	// Data record.
	$file = $folder.$scan[0];
	$record = fopen($file, "r");
	$data_items = fread($record, filesize($file));
	// Remove the redundant comma from the data record (scan).
	$data_items = substr($data_items, 0, -1);
	// Append the model result to the data record.
	$data_packet = $model_result."_".$data_items;
	// Pass the generated data packet.
	echo $data_packet;
    // Close the text file.
    fclose($record);
}

// If requested, create a CSV file from the stored aquatic ultrasonic scan samples.
if(isset($_GET["create"]) && $_GET["create"] == "csv"){
	create_CSV();
	echo "Server => CSV file created successfully!";
}

// If requested, pass the latest data record with the neural network model detection result.
if(isset($_GET["model_result"]) && $_GET["model_result"] == "OK"){
	get_latest_detection("./detection/");
}

?>