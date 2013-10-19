<?php

error_reporting(E_ALL);

$cxn = imap_open ("{mail.arsoft.homeip.net:143/imap/tls/novalidate-cert/debug}INBOX", "aroth", "mercur7", OP_HALFOPEN);
var_dump($cxn);

?>
