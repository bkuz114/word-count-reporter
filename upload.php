<?php
$tmp_file = "tmpfile.txt";  // rel this script
$report_path = "";
$txtFileType = strtolower(pathinfo($tmp_file, PATHINFO_EXTENSION));

$failures = array();

check_txt();
check_exists();
check_size();
check_format();
if (count($failures) === 0) {
	run_report();
}

$result = '<div id="result">';
if (count($failures) === 0) {
	$result .= '<div class="success">
					<h1>Success! Report generated at:</h1>
					<br>
					<h2>'.$report_path.'</h2>
				</div>';
} else {
	$result .= '<div class="failed">
					<h1>Failed! Failure reasons:</h1>
				<ul>';
	foreach ($failures as $x) {
  		$result .= "<li class='failure-messages'>$x</li>";
	}
	$result .= "</ul></div>";
}
$result .= "</div>";

echo '
<html>
<head>
	<title>Result</title>
	<style>
		body {
			background-color: gold;
		}
		#result {
			font-size: 18px;
			padding: 15px;
		}
		.failed {
			color: red;
		}
	</style>
</head>
<body>
	<h1>Result:</h1>
'.$result.'
</body>
</html>';

function check_txt() {
	global $failures;
	// Check if txt file is a actual txt or fake txt
	if (isset($_POST["submit"])) {
    	$check = filesize($_FILES["fileToUpload"]["tmp_name"]);
    	if ($check == false) {
        	$failures[] = "File is not an txt.";
    	}
	}
}

function check_exists() {
	global $failures;
	global $tmp_file;
	// Check if file already exists
	if (file_exists($tmp_file)) {
    	$failures[] = "Sorry, file $tmp_file already exists.";
	}
}

function check_size() {
	global $failures;
	// Check file size
	if ($_FILES["fileToUpload"]["size"] > 500000) {
    	$failures[] = "Sorry, your file is too large.";
	}
}

function check_format() {
	global $failures;
	global $txtFileType;
	// Allow certain file formats
	if ($txtFileType != "txt") {
    	$failures[] = "Sorry, only txt files are allowed.";
	}
}

function run_report() {
	global $failures;
	global $tmp_file;
	global $report_path;
    if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $tmp_file)) {
	    // call the python script
	    $pycall = "python word_count_reporter.py -i $tmp_file --usetitle";
	    if (isset($_POST["backup"])) {
	        $pycall .= " --backup";
	    }
	    $pycall .= " 2>&1";
	    exec($pycall, $output, $retval);
		if ($retval == 0) {
			$report_path = $output[0]; // path to report should be only output
		} else {
            $failures[] = "\nEncountered error code $retval when calling python. Error: ".var_export($output, true);
        }

        // delete the tmp file
        unlink($tmp_file);
    } else {
        $failures[] = "Sorry, there was an error uploading your file.";
    }
}
?>

