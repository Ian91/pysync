<?php

		$HOME = 'pysync_form.php';
		$MAIN_INTERFACE = 'main_interface.php';
		$CREATE_ACCOUNT_PAGE = 'create_account.php';


		function redirect($dest_page, $delay_seconds)
		{
			$delay_microseconds = $delay_seconds * 1000;

			echo "<br>If you are not redirected automatically, <a href='$dest_page'>click here.</a>";
			
			echo "
				 <script type='text/javascript'>
    			 window.setTimeout(function() {
        			 window.location.href='$dest_page';
    			 }, $delay_microseconds);
				 </script>
				 ";
		}			
					

	   function get_credentials()
	   {
			global $HOME;
			global $MAIN_INTERFACE;
			global $CREATE_ACCOUNT_PAGE;
	    
			echo "
				<html>
				<head>
					<title>Pysync Login</title>
				</head>
				<body>
				<form method='post' action='pysync_form.php'>
					Username:  <input type='text' name='username'>
					<br><br>		
					Password:  <input type='text' name='password'>
					<br><br>
					<input type='submit' value='Log In'>
				</form>
				</body>
				</html>
				 ";

			echo "
				<html>
				<body>
				<br>
				<form method='post' action='$HOME'>
					<input type='submit' name='create_account' value='Create Account'>
				</form>
				</body>
				</html>
				 ";

			if (isset($_POST['username']))
			{
				$username = $_POST['username'];
				$password = $_POST['password'];
				
				$cmd = "./check_password.py $username $password";
				exec($cmd, $output, $rv);				

				if ($rv != 0)
				{
					echo '<br>Invalid credentials ( got return code ' . $rv . ' ).';
				}
				else
				{
					echo 'Welcome, ' . $username . '.';
					$_SESSION['login'] = 'TRUE';
					$_SESSION['username'] = $username;
						
					redirect($MAIN_INTERFACE, 2);				
				}
			}

			if (isset($_POST['create_account']))
			{
				echo 'Proceeding to account creation...<br>';
				redirect($CREATE_ACCOUNT_PAGE, 0);
			}
	   }


		function show_files($username)
		{
			echo '<br>Your files are:<br><br>';

			$db_conn = new mysqli('localhost', 'pysync', 'sesame', 'pysync_backups');
			if ($db_conn->connect_errno > 0)
				die('database error: unable to connect');

			$query = ("SELECT file_name, modified_time, version FROM files INNER JOIN users ON files.user_id = users.user_id 
					   WHERE users.username = '$username'");		
			$result = $db_conn->query($query);
			if (!$result)
				die('files SELECT query failed');
		
			while ($row = $result->fetch_assoc())
			{
				echo "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" . $row['modified_time'] . " (version ". $row['version'] . "): &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" . 
						$row['file_name'] . "<br>";
			}
		}


		function log_out()
		{
			global $HOME;

			$_SESSION['login'] = 'FALSE';
			$_SESSION['username'] = '';
			$_SESSION['password'] = '';
			
			echo '<br><br>You are now logged out.';
			redirect($HOME, 2);
			die();
		}
?>
