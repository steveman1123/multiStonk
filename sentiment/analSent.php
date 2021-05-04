<?php
//the purpose of this is to generate word sentiment based on financial headlines
//there will be a second file/game that will attempt to profile and learn whether a headline means good news or bad news (and the confidence it has on it)
//TODO: try using the following to compress the page even more (and expand out to main website)
//if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip'))
//  ob_start("ob_gzhandler"); else ob_start();


//TODO: add scoring
//TODO: add multiple users
//TODO: add "accounts" (basically just usernames with associated scores) and display them

/*
* get a buttload of headlines saved in one big file
* pop through each of those until empty, then regen headline list
* vote on each headline
* explode headline text into individual words (removing punctuation)
* add scores to the output dict (of format {word:score} -> 0=neutral +=positive, -=negative connotation)
*/

/*
TODO:
add scoring
add comments
make things into their own functions
add file locking
make more adjustments for multiple users
remove words that are just numbers or are less than 2 letters long (also might want to remove words not in a real dict (like stock symbols))

for scores:
might be easiest to just have a scores file, have the user have a cookie with their username, then return back their score (that'd solve concurrency right away, and high scores)
*/


global $fileLocation;
global $symbFile;
global $headlinesFile;
global $unlistedLocation;

//set the working directory (this is where this file is assuming that there's a simple include '/path/to/this/file' file in the server document root)
$fileLocation = join("\\",array_slice(explode("\\",get_included_files()[1]),0,-1));
$unlistedLocation = $fileLocation."/../../stockStuff"; //location outside of the git repo
$symbFile = $unlistedLocation."/stockStuff/allSymbs.json"; //where all the nasdaq symbols are stored - TODO: may want to expand beyond just nasdaq
$headlinesFile = $unlistedLocation."/stockStuff/headlines.json"; //where the headlines are stored
$wordFile = $unlistedLocation."/stockStuff/wordScores.json"; //where the word sentiment is stored

//TODO: may want to adjust this using the PHP_OS string
if(!file_exists($symbFile)) { //create the file if it doesn't exist
  if(exec("python3 $fileLocation/allNdaq.py")) { //try running python3 (as linux standard)
    if(exec("py $fileLocation/allNdaq.py")) { //try running py (as windows standard)
      if(exec("python $fileLocation/allNdaq.py")) { //try running py (as windows aliased)
        throw new Exception("No python installation or file found");
    }
  }
}


//get $numHeads number of headlines for $symb from the internet
function getInternetHeadlines($symb, $numHeads) {
  $url = "https://api.nasdaq.com/api/news/topic/articlebysymbol?q=$symb%7Cstocks%26offset=0%26limit=$numHeads";
  
  if(substr_count(PHP_OS,"WIN")>0) { //is a windows system
    exec("powershell \$r = curl \"".$url."\" -UseBasicParsing ; \$r.content", $headlines); //use the windows PS curl
  } else {
    exec("curl -A 'test/1.0 (Linux)' $url",$headlines); //use the linux curl (TODO: may want to change the user agent?)
  }
  //use this for testing instead of the other getting it from the api all the time
  $headlines = json_decode($headlines[0],true)['data']; //isolate just the headline list after converting to json object
  return $headlines;
}


//get $n headlines for the specified $symb from the file or from the internet
function getHeadline($symb) {
  global $headlinesFile;
  global $fileLocation;
  //check that the headlines file exists
  if(file_exists($headlinesFile)) {
    //file exists, read it and get the headlines
    $headlines = (array)json_decode(file_get_contents($headlinesFile), true);
    //echo count(" $headlines ");
    if(count($headlines)<1) { //if none are remaining, get headlines from internet and write to file
      $numHeads = 15; #get this many headlines per request
      $headlines = getInternetHeadlines($symb, $numHeads); //get headlines rom the internet
      file_put_contents($fileLocation.'/headlines.json',json_encode($headlines)); //write the headlines to the file
      //var_dump($headlines);
    }
  } else { //file doesn't exist, get headlines from internet and write to file
    $headlines = getInternetHeadlines($symb, $numHeads);
    file_put_contents($fileLocation.'/headlines.json',$headlines);  
  }
   
  return $headlines[0]['title']; #return the first term in the array always
}

/*
we're going to ignore concurrent clients for now (may restructure later if we feel like it)
if isset post:
  ensure it has reaction and headline
    ensure headline is present in headlines (get the index of it)
      explode sentance, remove punct, add scores to score dict
      remove index of it
    else
      explode sentence and remove punct (clean text too) (may want to remove this functionality in concurrency update)
  else
    do nothing
else
  do what's currently being done (check for symbs, get new headlines, serve headline, etc)
*/

if(isset($_POST)) { //make sure post has data
  if(array_key_exists("head",$_POST) and array_key_exists("sent",$_POST)) { //make sure it has the right data
    $headList = (array)json_decode(file_get_contents($headlinesFile),true); //get the list of recorded headlines
    foreach($headList as $h) {
      $heads[] = $h['title'];
    }
    
    
    if(in_array($_POST['head'], $heads)) { //make sure that the headline is in the headline list

      $head = strtolower(preg_replace("/[^A-Za-z0-9\- ]/","",$_POST['head'])); //strip out special chars (other than alphanumerics)
      $wordList = explode(" ",$head); //split by spaces
      
      if(file_exists($wordFile)) {
        $wordScores = (array) json_decode(file_get_contents($wordFile),true); //load in the words with scores
      } else {
        $wordScores = [];
      }

      foreach($wordList as $w) { //loop thru every word in the headline
        if(array_key_exists($w, $wordScores)) { #if it's already present in the scores, then append to it
          $wordScores[$w] = array("sent" => (int) $wordScores[$w]['sent'] + (int) $_POST['sent'],
                              "votes" => (int) $wordScores[$w]['votes'] + 1
                            );
          
        } else { //if it's not already present in the scores, then init it
          $wordScores[$w] = array("sent" => (int)$_POST['sent'], "votes" => 1);
        }
      }

      file_put_contents($wordFile, json_encode($wordScores));
      
      $idx = array_search($_POST['head'],$headList); //find where it is
      array_splice($headList,$idx,1); //remove the headline from the headline list
      
      file_put_contents($headlinesFile,json_encode($headList));
      //echo "blah";
    } else { //else the headline is not in the headline list
      echo "eh"; //TODO: this can show up with concurrency, could address by simply skipping (not doing anything), or by using both and getting both votes in
    }
  }
}




$symbs = (array)json_decode(file_get_contents($symbFile, true)); //get all the symbols & company names from the file stored into a keyed array
$symb = array_rand($symbs);
$head = getHeadline($symb);
?>
 <!DOCTYPE html>

<html lang=en>
  <head>
    <title>Sentiment Analysis Game</title>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <style>
      html, body {
        width: 100%;
        height: 100%;
        font-family: sans-serif;
        margin: auto;
        text-align: center;
        font-size: 14pt;
      }
      
      button {
        border-radius: 10px;
        font-size: 24pt;
        background-color: #fff;
      }
      
      button:focus { background-color: #aaa; }
      
      #headline {
        width: 33%;
        margin: 0 auto;
      }

      #wrap { margin-top: 20%; }
      
      @media screen and (max-width: 640px){
        #headline { width: 90%; }
        #wrap { margin-top: 50%; }
      }
    </style>
  </head>
  <body>
    <div id="wrap">
      <form method="post">
        <p id="headline"><?php echo $head; ?></p>
        <input type="hidden" name="head" value="<?php echo $head; ?>"/>
        <p>
          <button type="submit" name="sent" value="-1">-</button>&emsp;
          <button type="submit" name="sent" value="0" autofocus>&#215;</button>&emsp;
          <button type="submit" name="sent" value="1">+</button>
        </p>
      </form>
    </div>
  </body>
</html>
