<?php
$target_file = "tmpfile.txt";  // rel this script
$uploadOk = 1;
$txtFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));

// Check if txt file is a actual txt or fake txt
if (isset($_POST["submit"])) {
    $check = filesize($_FILES["fileToUpload"]["tmp_name"]);
    if ($check !== false) {
        echo "File is a txt - $check.";
        $uploadOk = 1;
    } else {
        echo "File is not an txt.";
        $uploadOk = 0;
    }
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
        echo "The file ". htmlspecialchars(basename($_FILES["fileToUpload"]["name"])). " has been uploaded @ $target_file.";
        // call the python script
        exec("python word_count_reporter.py -i $target_file 2>&1", $output, $retval);
        echo "\nCalled python";
        var_dump($output);
        if ($retval != 0) {
            echo "\nEncountered error code $retval when calling python";
        }

        // delete the tmp file
        unlink($target_file);
        echo "\ndeleted temp file $target_file";
    } else {
        echo "Sorry, there was an error uploading your file.";
    }
}
?>

