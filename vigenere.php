<?php

class Vigenere {
    
    static $alphabet = "abcdefghijklmnopqrstuvwxyz ";
    
    static $blockSize = 5;
    
    public function get_unique_keys($password) {
        
        $unique_keys = "";
    
        for($i = 0; $i < strlen($password); $i++){
            $letter = $password[$i];
            
            if(strpos($unique_keys,$letter) === false){
                $unique_keys .= $letter;
            }
        }
        return $unique_keys;
    }    
    
    private function get_mixed_alphabet($unique_keys){
        $mixed_alphabet = [];
        
        $temp_alphabet = "";
        $temp_alphabet .= $unique_keys;
        
        echo $temp_alphabet;
        
        for($i=0; $i < strlen(self::$alphabet); $i++){
            $letter = self::$alphabet[$i];
            
            if(strpos($temp_alphabet,$letter) === false){
                $temp_alphabet .= $letter;
            }
        }
        
        for($b=0; $b < self::$blockSize; $b++){
            for($i=$b; $i < strlen($temp_alphabet);){
            
                array_push($mixed_alphabet,$temp_alphabet[$i]);
                $i = $i + self::$blockSize;
                
            }
        }
        return $mixed_alphabet;        
    }
    
    private function get_keys($password, $message){
        $keys = [];
        for ($i = 0; $i < strlen($message); $i++) {
            $len = $i % strlen($password);
            array_push($keys, $password[$len]);
        }
        return implode("",$keys);       
    }
    
    private function vigenere_table($mixed_alphabet) {
        $temp = [];
        $vigenere = [];
        
        for ($i=0; $i < count($mixed_alphabet); $i++) {
            $temp[$i] = [];
            for ($j = 0; $j < count($mixed_alphabet); $j++) {
                
                $temp_character = $i + $j;
                
                if ($temp_character >= count($mixed_alphabet)) {
                    $temp_character = $temp_character - count($mixed_alphabet);
                }
                /*push into two dimensional array*/
                $temp[$i][$j] = $mixed_alphabet[$temp_character];
            }
        }

        for($i=0; $i<count($temp);$i++)
            array_push($vigenere,implode("",$temp[$i]));

        return $vigenere;
    
    }
    
    public function encrypt($password, $msg){
        
        $password = strtolower($password);
        $msg = strtolower($msg);
        
        $cipher = [];
        
        $unique_keys = $this->get_unique_keys($password);
        
        echo $unique_keys.PHP_EOL;
        
        //refer to vigenere table as the key alphabet
        $table = $this->vigenere_table($this->get_mixed_alphabet($unique_keys));
        

        //load the key of the message*/	
        $keys = $this->get_keys($password, $msg);

        for ($i = 0; $i < strlen(self::$alphabet); $i++) {
            $key_alphabet = $table[$i];
            $key = self::$alphabet[$i];
            $cipher[$key] = $key_alphabet;
        }
        
 
        $encrypted_message = "";

        for ($i = 0; $i < strlen($msg); $i++) {
            $msg_char = $msg[$i];
            $msg_key = $keys[$i];
            $tmp_alphabet = $cipher[$msg_key];
            $msg_char_index = strpos(self::$alphabet,$msg_char);
            $encrypted_char = $tmp_alphabet[$msg_char_index];

            $encrypted_message .= $encrypted_char;
        }
        return $encrypted_message;
    }
    
    public function decrypt($password, $cipher_msg){
        $password = strtolower($password);
        $cipher_msg = strtolower($cipher_msg);
        
        $decipher = [];
        
        $unique_keys = $this->get_unique_keys($password);
        
        $table = $this->vigenere_table($this->get_mixed_alphabet($unique_keys));
        
        $keys = $this->get_keys($password, $cipher_msg);

        for ($i = 0; $i < strlen(self::$alphabet); $i++) {
            $key_alphabet = $table[$i];
            $key = self::$alphabet[$i];
            $decipher[$key] = $key_alphabet;
        }


        $decrypted_message = "";
        
        for ($i = 0; $i < strlen($cipher_msg); $i++) {
            $decipher_msg_char = $cipher_msg[$i];
            $decipher_msg_key = $keys[$i];
            $temp_alphabet = $decipher[$decipher_msg_key];
            $decipher_msg_char_index = strpos($temp_alphabet,$decipher_msg_char);

            $decrypted_char = self::$alphabet[$decipher_msg_char_index];

            $decrypted_message .= $decrypted_char;
        }
        
       return $decrypted_message;    
    }
    
}

$v = new Vigenere();

$message = "now is the time for all good men to come to the aid of their fellow man";
$password = "excalibur";
$encrypted_message = $v->encrypt($password,$message);
$decrypted_message = $v->decrypt($password,$encrypted_message);

echo "Encrypted message: ". $encrypted_message.PHP_EOL;
echo "Decrypted message: ". $decrypted_message.PHP_EOL;
