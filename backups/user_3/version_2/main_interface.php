<?php		
	session_start();

	if (file_exists('form_functions.php')) 
	{	
		require_once 'form_functions.php';
	}
	else 
	{ 
		die('server file access error');	
	}



	$HOME = 'pysync_form.php';
	$HERE = 'main_interface.php';
	

	if (isset($_POST['log_out']))
	{
		log_out();
	}		


	if ($_SESSION['login'] == 'TRUE')
	{
		$username = $_SESSION['username'];

		echo "<br>
			 <form method='post' action='$HERE'>
			 <input type='submit' name='show_files' value='Show Files'>
			 </form>
			 ";

		if (isset($_POST['show_files']))
		{
			show_files($username);
		}

		echo '<br><br>You are logged in as ' . $username . '.';
		echo '
			 <form method="post" action="main_interface.php">
			 <br><input type="submit" name="log_out" value="Log Out">
			 </form>
			 ';
	}

	else
	{
		echo '<br>You are not logged in.';
		redirect($HOME, 2);
	}

?>	
