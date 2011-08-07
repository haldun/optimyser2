(function(){
  var days = 360;
  var id='{{ experiment.key().name() }}';
  var createCookie = function(name,value) {
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
  };
  var selected_index = readCookie(id);
  document.write('<sc' + 'ript src="' +
    '//{{ request.host }}{{ reverse_url('options') }}?e=' + id +
    '&h=' + escape(document.location.hash.substr(1)) +
    '&s=' + (selected_index ? selected_index : '') +
    '"></sc'+'ript>');
})();
