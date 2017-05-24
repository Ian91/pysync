<?php
	
	if (file_exists('form_functions.php')) 
	{	
		require_once 'form_functions.php';
	}
	else 
	{ 
		die('server file access error');	
	}


	$HERE = 'create_account.php';
	$HOME = 'pysync_form.php';

    echo "
		 <html>
		 <head>
		 <title>Create Account</title>
		 </head>
		 <body>
		 Create your account:
		 <br><br>
		 <form method='post' action='$HERE'>
			 Username:  <input type='text' name='username'>
			 <br><br>		
			 Password:  <input type='text' name='password'>
			 <br><br>
			 <input type='submit' value='Create Account'>
		 </form>
		 </body>
		 </html>
		 ";

    if (isset($_POST['username']))
	{
		$proposed_username = $_POST['username'];
		$proposed_password = $_POST['password'];

		$cmd = "./create_account.py $proposed_username $proposed_password"; 
		exec($cmd, $output, $return_code);
		if ($return_code == 0)
		{
			echo '<br>Account created successfully! Please log in.';
			redirect($HOME, 2);	
		}
		else
		{
			echo 'error in creating account: got return code ' . $return_code;
		}
	} 

?>
