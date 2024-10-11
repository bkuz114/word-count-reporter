<?php
$target_file = "tmpfile.txt";  // rel this script
$uploadOk = 1;
$txtFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
$report = "";

// Check if txt file is a actual txt or fake txt
if (isset($_POST["submit"])) {
    $check = filesize($_FILES["fileToUpload"]["tmp_name"]);
    if ($check !== false) {
        $uploadOk = 1;
    } else {
        echo "File is not an txt.";
        $uploadOk = 0;
    }
    // Check if file already exists
    if (file_exists($target_file)) {
        echo "Sorry, file already exists.";
        $uploadOk = 0;
    }

    // Check file size
    if ($_FILES["fileToUpload"]["size"] > 500000) {
        echo "Sorry, your file is too large.";
        $uploadOk = 0;
    }

    // Allow certain file formats
    if ($txtFileType != "txt") {
        echo "Sorry, only JPG, JPEG, PNG & GIF files are allowed.";
        $uploadOk = 0;
    }

    // Check if $uploadOk is set to 0 by an error
    if ($uploadOk == 0) {
        echo "Sorry, your file was not uploaded.";
        // if everything is ok, try to upload file
    } else {
        if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
            // call the python script
            exec("python word_count_reporter.py -i $target_file 2>&1", $output, $retval);
            if ($retval != 0) {
                echo "\nEncountered error code $retval when calling python";
			}
			$report = $output[0];

            // delete the tmp file
            unlink($target_file);
        } else {
            echo "Sorry, there was an error uploading your file.";
        }
    }

}

?>


<html>

<head>
    <link rel="icon" href="./favicon.ico">
    <style>
        body {
            background-color: dodgerblue;
            font-size: 20px;
            padding: 5px 0px 0px 15px;
        }

        input {
            font-size: 20px;
        }

        #wrapper {
            padding-top: 20px;
		}

		#inner-report {
			font-weight: bolder;
			padding: 5px;
		}
    </style>
</head>

<body>

    <h1>Select input file to generate report from.</h1>
	
    <div id="wrapper">
        <form action="" method="post" enctype="multipart/form-data">
            <input type="file" name="fileToUpload" id="fileToUpload">
            <input type="submit" value="Generate Report" name="submit" id="submit" disabled>
        </form>
    </div>

	<div id="report-info" style="display: none;">
		Report:
		<br>
		<div id="inner-report">
		</div>
	</div>

	<script>
        document.getElementById("fileToUpload").onchange = function() {
            document.getElementById("submit").disabled = false;
		};
		var php = "<?php echo addslashes($report); ?>";
		if (php) {
			//document.getElementById("inner-report").innerHTML = `<a href="${linkpath}" target="_blank">${linkpath}</a>`;
			document.getElementById("inner-report").innerHTML = php;
			document.getElementById("report-info").style.display = 'block';
		}
    </script>
</body>

</html>
