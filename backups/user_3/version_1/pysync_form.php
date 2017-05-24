<?php
	session_start();

	$MAIN_INTERFACE = 'main_interface.php';


	if (file_exists('form_functions.php')) 
	{	
		require_once 'form_functions.php';
	}
	else 
	{ 
		die('server file access error');	
	}


	if ($_SESSION['login'] != 'TRUE')
	{
		get_credentials();
	}
	else
	{
		echo '<br>You are already logged in.<br>';
		redirect($MAIN_INTERFACE, 3);
	}
?>
