(function(){
var createCookie = function(name,value,days) {
	if (days) {
		var date = new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
	}
	else var expires = "";
	document.cookie = name+"="+value+expires+"; path=/";
};

var readCookie = function(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for(var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

var eraseCookie = function(name) {
	createCookie(name,"",-1);
}

var index = {{ index }};

createCookie('opt_e', "{{ experiment.key().name() }}");
createCookie('opt_i', "{{ index }}");

if (document.location.href != "{{ next }}") {
  document.location.href = "{{ next }}";
}
})();
