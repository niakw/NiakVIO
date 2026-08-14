/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */
;(function(g,rules){
  if(!g||typeof g.fetch!=="function")return;
  var key="__nuvioDomainOverrideV1";
  var state=g[key];
  if(!state){
    state={native:g.fetch.bind(g),rules:Object.create(null)};
    g[key]=state;
    g.fetch=function(input,init){
      var next=input;
      try{
        var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
        var url=new URL(raw);
        var replacement=state.rules[String(url.hostname).toLowerCase()];
        if(replacement){
          url.hostname=replacement;
          next=(typeof Request!=="undefined"&&input instanceof Request)?new Request(url.toString(),input):url.toString();
        }
      }catch(_error){}
      return state.native(next,init);
    };
  }
  for(var i=0;i<rules.length;i++){
    try{state.rules[atob(rules[i][0])]=rules[i][1];}catch(_error){}
  }
})(typeof globalThis!=="undefined"?globalThis:this,[["bmV3MS5tb3ZpZXNkcml2ZS5jaHJpc3RtYXM=","new2.moviesdrive.christmas"],["bmV3My5tb3ZpZXNkcml2ZXMubXk=","new2.moviesdrive.christmas"]]);
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */
;(function(g,encoded){
  if(!g||typeof g.fetch!=="function"||g.__nuvioAdaptiveDomainRecoveryV1)return;
  var nativeFetch=g.fetch.bind(g), groups=[];
  try{
    var decoded=JSON.parse(typeof atob==="function"?atob(encoded):Buffer.from(encoded,"base64").toString("utf8"));
    groups=Array.isArray(decoded)?decoded:(decoded&&Array.isArray(decoded.groups)?decoded.groups:[]);
  }catch(_e){return;}
  var cache=Object.create(null);
  function obsolete(status){return status===403||status===404||status===408||status===410||status===425||status===429||status===451||status===500||status===502||status===503||status===504||(status>=520&&status<=524);}
  function groupFor(host){
    host=String(host||"").toLowerCase();
    for(var i=0;i<groups.length;i++)if(groups[i].hosts.indexOf(host)!==-1)return groups[i];
    return null;
  }
  function rebuild(raw,origin){
    var source=new URL(raw), target=new URL(origin);
    target.pathname=source.pathname; target.search=source.search; target.hash=source.hash;
    return target.toString();
  }
  function cloneInput(input,url){
    try{return typeof Request!=="undefined"&&input instanceof Request?new Request(url,input):url;}catch(_e){return url;}
  }
  function attempt(input,init,raw,group,index){
    if(index>=group.candidates.length)return nativeFetch(input,init);
    var origin=group.candidates[index], url;
    try{url=rebuild(raw,origin);}catch(_e){return attempt(input,init,raw,group,index+1);}
    return nativeFetch(cloneInput(input,url),init).then(function(response){
      if(response&&!obsolete(response.status)){
        try{cache[new URL(raw).hostname.toLowerCase()]=origin;}catch(_e){}
        return response;
      }
      return attempt(input,init,raw,group,index+1);
    },function(){return attempt(input,init,raw,group,index+1);});
  }
  g.fetch=function(input,init){
    var raw;
    try{raw=typeof Request!=="undefined"&&input instanceof Request?input.url:String(input);}catch(_e){return nativeFetch(input,init);}
    var parsed, group;
    try{parsed=new URL(raw);group=groupFor(parsed.hostname);}catch(_e){return nativeFetch(input,init);}
    if(!group)return nativeFetch(input,init);
    var remembered=cache[parsed.hostname.toLowerCase()];
    if(remembered){
      var preferred=[remembered], rest=[];
      for(var i=0;i<group.candidates.length;i++)if(group.candidates[i]!==remembered)rest.push(group.candidates[i]);
      group={hosts:group.hosts,candidates:preferred.concat(rest)};
    }
    return attempt(input,init,raw,group,0);
  };
  g.__nuvioAdaptiveDomainRecoveryV1=true;
})(typeof globalThis!=="undefined"?globalThis:this,"eyJncm91cHMiOlt7ImNhbmRpZGF0ZXMiOlsiaHR0cHM6Ly9uZXc3Lm1vdmllc2RyaXZlcy5teSJdLCJob3N0cyI6WyJuZXczLm1vdmllc2RyaXZlcy5teSJdfV0sInJldmlzaW9uIjoicmV0cnktdHJhbnNpZW50LXYyIn0=");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */
var _0x14577e=_0x45eb;(function(_0x5ef636,_0x5d9d3b){var _0x26ac91={_0x2a46f8:0xc8,_0x1be863:0xcd,_0x17b074:0xf8,_0x526fc1:0x10b,_0x2d7b25:0xfb},_0x26eb91=_0x45eb,_0x3a886b=_0x5ef636();while(!![]){try{var _0x1ce1ca=-parseInt(_0x26eb91(_0x26ac91._0x2a46f8))/0x1+-parseInt(_0x26eb91(0xc2))/0x2*(parseInt(_0x26eb91(_0x26ac91._0x1be863))/0x3)+-parseInt(_0x26eb91(_0x26ac91._0x17b074))/0x4+parseInt(_0x26eb91(_0x26ac91._0x526fc1))/0x5+parseInt(_0x26eb91(0xcc))/0x6*(-parseInt(_0x26eb91(0xda))/0x7)+-parseInt(_0x26eb91(_0x26ac91._0x2d7b25))/0x8+parseInt(_0x26eb91(0xf5))/0x9;if(_0x1ce1ca===_0x5d9d3b)break;else _0x3a886b['push'](_0x3a886b['shift']());}catch(_0x2a23a0){_0x3a886b['push'](_0x3a886b['shift']());}}}(_0x40ed,0x9e990));var __defProp=Object['defineProperty'],__defProps=Object[_0x14577e(0xbe)],__getOwnPropDescs=Object['getOwnPropertyDescriptors'],__getOwnPropSymbols=Object['getOwnPropertySymbols'],__hasOwnProp=Object[_0x14577e(0xe3)][_0x14577e(0xf3)],__propIsEnum=Object[_0x14577e(0xe3)]['propertyIsEnumerable'],__defNormalProp=(_0x3272b6,_0x399934,_0x1ac766)=>_0x399934 in _0x3272b6?__defProp(_0x3272b6,_0x399934,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x1ac766}):_0x3272b6[_0x399934]=_0x1ac766,__spreadValues=(_0x4f21cf,_0x4c151c)=>{var _0xf5f734={_0x5b5dd6:0xcf},_0x9a3425=_0x14577e;for(var _0x5e9416 in _0x4c151c||(_0x4c151c={}))if(__hasOwnProp['call'](_0x4c151c,_0x5e9416))__defNormalProp(_0x4f21cf,_0x5e9416,_0x4c151c[_0x5e9416]);if(__getOwnPropSymbols)for(var _0x5e9416 of __getOwnPropSymbols(_0x4c151c)){if(__propIsEnum[_0x9a3425(_0xf5f734._0x5b5dd6)](_0x4c151c,_0x5e9416))__defNormalProp(_0x4f21cf,_0x5e9416,_0x4c151c[_0x5e9416]);}return _0x4f21cf;},__spreadProps=(_0x28edc4,_0x58cfc7)=>__defProps(_0x28edc4,__getOwnPropDescs(_0x58cfc7)),__async=(_0x22f6ae,_0x30586e,_0x1d8812)=>{return new Promise((_0x256e5f,_0xf430ad)=>{var _0xeaaeb7=_0x45eb,_0x53316d=_0x32b96=>{try{_0x1ce7e4(_0x1d8812['next'](_0x32b96));}catch(_0x3a6b11){_0xf430ad(_0x3a6b11);}},_0x259e89=_0x259095=>{try{_0x1ce7e4(_0x1d8812['throw'](_0x259095));}catch(_0x4a4748){_0xf430ad(_0x4a4748);}},_0x1ce7e4=_0x1f8980=>_0x1f8980['done']?_0x256e5f(_0x1f8980[_0xeaaeb7(0xc9)]):Promise['resolve'](_0x1f8980['value'])[_0xeaaeb7(0xde)](_0x53316d,_0x259e89);_0x1ce7e4((_0x1d8812=_0x1d8812[_0xeaaeb7(0xed)](_0x22f6ae,_0x30586e))['next']());});},PROVIDER_NAME='MoviesDrive',MAIN_URL=_0x14577e(0xf0),ARCHIVE_DOMAIN='https://mdrive.lol',TMDB_KEY=_0x14577e(0xe1),MOBILE_UAS=[_0x14577e(0x102),'Mozilla/5.0\x20(Linux;\x20Android\x2013;\x20SM-S918B)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/116.0.0.0\x20Mobile\x20Safari/537.36','Mozilla/5.0\x20(Linux;\x20Android\x2012;\x20Pixel\x206)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/115.0.0.0\x20Mobile\x20Safari/537.36','Mozilla/5.0\x20(iPhone;\x20CPU\x20iPhone\x20OS\x2017_0\x20like\x20Mac\x20OS\x20X)\x20AppleWebKit/605.1.15\x20(KHTML,\x20like\x20Gecko)\x20Version/17.0\x20Mobile/15E148\x20Safari/604.1','Mozilla/5.0\x20(iPad;\x20CPU\x20OS\x2017_0\x20like\x20Mac\x20OS\x20X)\x20AppleWebKit/605.1.15\x20(KHTML,\x20like\x20Gecko)\x20Version/17.0\x20Mobile/15E148\x20Safari/604.1'];function getHeaders(_0x4c32e0){var _0x5433be={_0x39e7b4:0x104,_0x59d5b3:0x106},_0x144401=_0x14577e,_0x3d37cf=MOBILE_UAS[Math['floor'](Math[_0x144401(_0x5433be._0x39e7b4)]()*MOBILE_UAS[_0x144401(0xd2)])],_0x1ec7d3={'User-Agent':_0x3d37cf,'Accept-Language':_0x144401(_0x5433be._0x59d5b3)};if(_0x4c32e0)for(var _0x374c2c in _0x4c32e0){_0x1ec7d3[_0x374c2c]=_0x4c32e0[_0x374c2c];}return _0x1ec7d3;}function log(_0x378ba4){var _0x5553d8=_0x14577e;console[_0x5553d8(0xbc)]('['+PROVIDER_NAME+']\x20'+_0x378ba4);}function err(_0x1add6f){var _0x2fe214={_0x49004c:0xea},_0x1a32ae=_0x14577e;console[_0x1a32ae(_0x2fe214._0x49004c)]('['+PROVIDER_NAME+']\x20'+_0x1add6f);}function fetchText(_0x5a52cd,_0x5f21e1,_0x279565){var _0x247a56={_0x4744c7:0xfe,_0x1ea28d:0xc4,_0x205fb4:0xba,_0x214759:0xf4};return __async(this,null,function*(){var _0x5bfbf8={_0x44f451:0xce},_0xbe9a3a=_0x45eb;_0x279565=_0x279565||0x2ee0;try{var _0x31fe40=null;if(typeof AbortSignal!=='undefined'&&AbortSignal['timeout'])_0x31fe40=AbortSignal['timeout'](_0x279565);var _0x1c6bd5=getHeaders(_0x5f21e1&&_0x5f21e1[_0xbe9a3a(_0x247a56._0x4744c7)]?null:null);if(_0x5f21e1&&_0x5f21e1[_0xbe9a3a(0xfe)])for(var _0x35a6ff in _0x5f21e1['headers']){_0x1c6bd5[_0x35a6ff]=_0x5f21e1[_0xbe9a3a(_0x247a56._0x4744c7)][_0x35a6ff];}var _0x37987a=__spreadProps(__spreadValues({},_0x5f21e1||{}),{'headers':_0x1c6bd5});if(_0x31fe40)_0x37987a[_0xbe9a3a(_0x247a56._0x1ea28d)]=_0x31fe40;var _0x9ef474=fetch(_0x5a52cd,_0x37987a),_0x4b646e=new Promise(function(_0x24f719,_0x586256){setTimeout(function(){var _0x5e8da0=_0x45eb;_0x586256(new Error(_0x5e8da0(_0x5bfbf8._0x44f451)+_0x279565+'ms'));},_0x279565);}),_0x174f8a=yield Promise[_0xbe9a3a(0xdc)]([_0x9ef474,_0x4b646e]);if(_0x174f8a['ok'])return yield _0x174f8a['text']();return null;}catch(_0x3872b6){return err(_0xbe9a3a(_0x247a56._0x205fb4)+_0x5a52cd['substring'](0x0,0x50)+_0xbe9a3a(0x109)+(_0x3872b6[_0xbe9a3a(_0x247a56._0x214759)]||'')),null;}});}function _0x45eb(_0x4e1cd3,_0x1973e5){_0x4e1cd3=_0x4e1cd3-0xb4;var _0x40ed16=_0x40ed();var _0x45ebed=_0x40ed16[_0x4e1cd3];if(_0x45eb['Ujkizb']===undefined){var _0x5c623e=function(_0xba5b09){var _0x1432fc='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';var _0x3272b6='',_0x399934='';for(var _0x1ac766=0x0,_0x4f21cf,_0x4c151c,_0x5e9416=0x0;_0x4c151c=_0xba5b09['charAt'](_0x5e9416++);~_0x4c151c&&(_0x4f21cf=_0x1ac766%0x4?_0x4f21cf*0x40+_0x4c151c:_0x4c151c,_0x1ac766++%0x4)?_0x3272b6+=String['fromCharCode'](0xff&_0x4f21cf>>(-0x2*_0x1ac766&0x6)):0x0){_0x4c151c=_0x1432fc['indexOf'](_0x4c151c);}for(var _0x28edc4=0x0,_0x58cfc7=_0x3272b6['length'];_0x28edc4<_0x58cfc7;_0x28edc4++){_0x399934+='%'+('00'+_0x3272b6['charCodeAt'](_0x28edc4)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x399934);};_0x45eb['srmacr']=_0x5c623e,_0x45eb['BPoibd']={},_0x45eb['Ujkizb']=!![];}var _0x440df4=_0x40ed16[0x0],_0x4b1ea5=_0x4e1cd3+_0x440df4,_0x5e7fc6=_0x45eb['BPoibd'][_0x4b1ea5];return!_0x5e7fc6?(_0x45ebed=_0x45eb['srmacr'](_0x45ebed),_0x45eb['BPoibd'][_0x4b1ea5]=_0x45ebed):_0x45ebed=_0x5e7fc6,_0x45ebed;}function fetchJson(_0x255ec3,_0x527d87,_0x4897d8){return __async(this,null,function*(){var _0x3c6852=yield fetchText(_0x255ec3,_0x527d87,_0x4897d8);if(!_0x3c6852)return null;try{return JSON['parse'](_0x3c6852);}catch(_0x22c65a){return null;}});}function parseQuality(_0x411be7){var _0x302eb2={_0x58c1d2:0xfa,_0x527fec:0xd8},_0x22e7c5=_0x14577e,_0x420f81=String(_0x411be7||''),_0x5a0a80=_0x420f81[_0x22e7c5(_0x302eb2._0x58c1d2)](/(2160|1080|720|480)\s*P/i);if(_0x5a0a80)return _0x5a0a80[0x1]+'p';if(/4K|UHD/i[_0x22e7c5(0xe5)](_0x420f81))return _0x22e7c5(0x101);if(/1440|2K/i['test'](_0x420f81))return _0x22e7c5(_0x302eb2._0x527fec);return'HD';}function extractSiteTitle(_0x53d09e){var _0x1c7bd6=_0x14577e,_0x29f75b=_0x53d09e['match'](/<title>(.*?)<\/title>/i);if(!_0x29f75b)return'';var _0x150695=_0x29f75b[0x1],_0x5bc783=_0x150695[_0x1c7bd6(0xfa)](/Download\s+(.+?)\s+(?:In HD Free|Free Download)/i);if(_0x5bc783)return _0x5bc783[0x1][_0x1c7bd6(0xd7)]();var _0x566017=_0x150695[_0x1c7bd6(0xe4)](/^(?:Download\s+)?/,'');return _0x566017=_0x566017['replace'](/\s+(?:\d{3,4}p\b|4K\b|WEB-DL\b|BluRay\b|HDTV\b|x26[45]\b|HEVC\b|SDR\b|HDR\b|DD\d|DDP\d|Hindi|English|Dual\s*Audio|ESubs?)\b.*$/i,''),_0x566017=_0x566017[_0x1c7bd6(0xe4)](/\s*[-–|]\s*\w*\s*$/i,'')[_0x1c7bd6(0xd7)](),_0x566017=_0x566017['replace'](/&#8211;/g,'–'),_0x566017||_0x150695;}function isStrictMatch(_0xb452e1,_0x12bf51,_0x41ea32,_0x470edb){var _0x3e9bb5={_0x3c1332:0xb8,_0x56712f:0xe4,_0xfacc84:0xd2},_0x45f8a5=_0x14577e;if(!_0xb452e1||!_0x41ea32)return![];var _0x531bf0=_0xb452e1[_0x45f8a5(_0x3e9bb5._0x3c1332)]()['replace'](/[^a-z0-9\s]/g,'\x20')['trim']()[_0x45f8a5(_0x3e9bb5._0x56712f)](/\s+/g,'\x20'),_0x46d8c6=_0x41ea32['toLowerCase']()[_0x45f8a5(0xe4)](/download\s*/g,'')[_0x45f8a5(_0x3e9bb5._0x56712f)](/[^a-z0-9\s]/g,'\x20')['trim']()['replace'](/\s+/g,'\x20');if(_0x46d8c6!==_0x531bf0&&_0x46d8c6[_0x45f8a5(0xb5)](_0x531bf0+'\x20')!==0x0&&_0x46d8c6['indexOf']('\x20'+_0x531bf0+'\x20')===-0x1&&_0x46d8c6['indexOf']('\x20'+_0x531bf0)!==_0x46d8c6[_0x45f8a5(_0x3e9bb5._0xfacc84)]-_0x531bf0[_0x45f8a5(0xd2)]-0x1)return![];if(_0x12bf51&&_0x470edb){var _0x14ae77=parseInt(_0x12bf51),_0x3e00d9=parseInt(_0x470edb);if(!isNaN(_0x14ae77)&&!isNaN(_0x3e00d9)&&Math['abs'](_0x14ae77-_0x3e00d9)>0x1)return![];}return!![];}function extractSeasonHtml(_0x3be84a,_0x30890e){var _0x5314af={_0x279f70:0xf1,_0x2996ea:0xe0,_0x43111a:0xd2,_0x1a070d:0xf1,_0x586601:0x107},_0x2920aa=_0x14577e;if(!_0x3be84a||_0x30890e==null)return _0x3be84a;var _0x30854d=new RegExp(_0x2920aa(0xbb),'gi'),_0xd1ee0f,_0x14b86b=[];while((_0xd1ee0f=_0x30854d['exec'](_0x3be84a))!==null){_0x14b86b['push']({'index':_0xd1ee0f['index'],'season':parseInt(_0xd1ee0f[0x2])});}var _0x5e77ad=-0x1,_0x43535d=-0x1;for(var _0x465de4=0x0;_0x465de4<_0x14b86b[_0x2920aa(0xd2)];_0x465de4++){if(_0x14b86b[_0x465de4][_0x2920aa(_0x5314af._0x279f70)]===_0x30890e){if(_0x5e77ad===-0x1)_0x5e77ad=_0x465de4;}else _0x43535d=_0x465de4;}if(_0x5e77ad===-0x1){var _0xe3fda5=new RegExp(_0x2920aa(_0x5314af._0x2996ea),'gi'),_0x2675eb,_0x54904f=-0x1;while((_0x2675eb=_0xe3fda5['exec'](_0x3be84a))!==null){if(_0x30890e>=parseInt(_0x2675eb[0x2])&&_0x30890e<=parseInt(_0x2675eb[0x3])){_0x54904f=_0x2675eb['index'];break;}}if(_0x54904f!==-0x1)return _0x3be84a['substring'](_0x54904f);return null;}var _0x7c0492=_0x14b86b[_0x5e77ad]['index'];if(_0x43535d>_0x5e77ad)for(var _0x51a624=0x0;_0x51a624<_0x14b86b[_0x2920aa(0xd2)];_0x51a624++){if(_0x14b86b[_0x51a624][_0x2920aa(0xf1)]===_0x30890e&&_0x51a624>_0x43535d){_0x7c0492=_0x14b86b[_0x51a624]['index'];break;}}var _0x45af5f=_0x3be84a['length'];for(var _0x51a624=0x0;_0x51a624<_0x14b86b[_0x2920aa(_0x5314af._0x43111a)];_0x51a624++){if(_0x14b86b[_0x51a624]['index']>_0x7c0492&&_0x14b86b[_0x51a624][_0x2920aa(_0x5314af._0x1a070d)]!==_0x30890e){_0x45af5f=_0x14b86b[_0x51a624][_0x2920aa(_0x5314af._0x586601)];break;}}return _0x3be84a['substring'](_0x7c0492,_0x45af5f);}function getMedia(_0x2f21db,_0x242d05){var _0x5a96a8={_0x2eca9b:0xdb,_0xd2a83d:0xd2,_0x195d23:0xef,_0x17580a:0xd4};return __async(this,null,function*(){var _0x36a15c=_0x45eb,_0x9abe02=String(_0x2f21db||'')['trim'](),_0xd06be4=_0x9abe02['indexOf']('tt')===0x0,_0x15a301=_0x242d05==='tv'||_0x242d05==='series'?'tv':_0x36a15c(_0x5a96a8._0x2eca9b);try{if(_0xd06be4){var _0x3d41ae=yield fetchJson('https://api.themoviedb.org/3/find/'+_0x9abe02+'?api_key='+TMDB_KEY+'&external_source=imdb_id',{},0x2710),_0x4a3636=_0x3d41ae?_0x15a301==='tv'?_0x3d41ae[_0x36a15c(0xd0)]:_0x3d41ae['movie_results']:null;if(_0x4a3636&&_0x4a3636[_0x36a15c(_0x5a96a8._0xd2a83d)]>0x0){var _0x3078e3=_0x4a3636[0x0];return{'title':_0x15a301==='tv'?_0x3078e3['name']:_0x3078e3[_0x36a15c(0xd4)],'year':(_0x3078e3[_0x36a15c(0xec)]||_0x3078e3[_0x36a15c(0xb6)]||'')[_0x36a15c(_0x5a96a8._0x195d23)]('-')[0x0],'imdb':_0x9abe02};}}else{var _0x3d41ae=yield fetchJson(_0x36a15c(0x103)+_0x15a301+'/'+_0x9abe02+'?api_key='+TMDB_KEY+_0x36a15c(0xbd),{},0x2710);if(_0x3d41ae)return{'title':_0x15a301==='tv'?_0x3d41ae['name']:_0x3d41ae[_0x36a15c(_0x5a96a8._0x17580a)],'year':(_0x3d41ae['first_air_date']||_0x3d41ae[_0x36a15c(0xb6)]||'')['split']('-')[0x0],'imdb':_0x3d41ae['imdb_id']||_0x3d41ae['external_ids']&&_0x3d41ae[_0x36a15c(0xbf)][_0x36a15c(0xca)]||null};}}catch(_0x4ce5f1){err('tmdb:\x20'+_0x4ce5f1['message']);}return{'title':_0x9abe02,'year':null,'imdb':null};});}function searchSite(_0x42ef8f){var _0x5e80ab={_0x1fe8be:0xcb,_0x48b839:0xc5,_0x306e4b:0xd2};return __async(this,null,function*(){var _0x3d91e7=_0x45eb,_0x40ca62=encodeURIComponent(_0x42ef8f),_0x15afcd=MAIN_URL+_0x3d91e7(0xb4)+_0x40ca62+'&per_page=10',_0x1d9e42=yield fetchJson(_0x15afcd,{'headers':{'Referer':MAIN_URL+'/'}},0x2710);if(!_0x1d9e42||!_0x1d9e42[_0x3d91e7(0x100)]||_0x1d9e42[_0x3d91e7(0x100)][_0x3d91e7(0xd2)]===0x0)return log(_0x3d91e7(0xe8)+_0x42ef8f),[];var _0x370c4c=[];for(var _0x42db53=0x0;_0x42db53<_0x1d9e42['hits'][_0x3d91e7(0xd2)];_0x42db53++){var _0x4175eb=_0x1d9e42[_0x3d91e7(0x100)][_0x42db53]['document'];if(_0x4175eb&&_0x4175eb[_0x3d91e7(0x10d)]&&_0x4175eb['post_title']){var _0x1e72d4=_0x4175eb[_0x3d91e7(0xc5)][_0x3d91e7(0xfa)](/\((\d{4})\)/);_0x370c4c[_0x3d91e7(_0x5e80ab._0x1fe8be)]({'title':_0x4175eb[_0x3d91e7(_0x5e80ab._0x48b839)],'href':_0x4175eb['permalink'],'year':_0x1e72d4?parseInt(_0x1e72d4[0x1]):null,'imdb':_0x4175eb['imdb_id']||null});}}return log(_0x3d91e7(0x10c)+_0x370c4c[_0x3d91e7(_0x5e80ab._0x306e4b)]+_0x3d91e7(0xd5)+_0x42ef8f),_0x370c4c;});}function parsePage(_0x5e741d,_0x90f03,_0x23c796){var _0x468864={_0x2984e1:0xe2};return __async(this,null,function*(){var _0x20c3c1=_0x45eb;if(!_0x23c796)_0x23c796=yield fetchText(_0x5e741d,{'headers':{'Referer':MAIN_URL+'/'}},0x2ee0);if(!_0x23c796)return[];var _0x28c5d6=_0x90f03!=null,_0x28bfc0=_0x28c5d6?extractSeasonHtml(_0x23c796,_0x90f03):_0x23c796;if(!_0x28bfc0)return log('season\x20'+_0x90f03+_0x20c3c1(0xee)),[];var _0x4312f0=[],_0x6039b0=/href="(https?:\/\/mdrive\.lol\/archive\/(\d+)[^"]*)"[^>]*>([\s\S]*?)<\/a>/gi,_0x3d3df3;while((_0x3d3df3=_0x6039b0['exec'](_0x28bfc0))!==null){var _0xd91ee5=_0x3d3df3[0x3]['replace'](/<[^>]+>/g,'')['trim']();if(_0x28c5d6&&/zip/i[_0x20c3c1(0xe5)](_0xd91ee5))continue;var _0x2460c6=parseQuality(_0xd91ee5);if(_0x2460c6==='480p')continue;var _0x46a7f5=_0xd91ee5['match'](/\[([\d.]+)\s*(MB|GB|TB)\]/i),_0x1813ac=_0x46a7f5?_0x46a7f5[0x0]:'';_0x4312f0['push']({'id':_0x3d3df3[0x2],'url':_0x3d3df3[0x1],'label':_0xd91ee5,'q':_0x2460c6,'size':_0x1813ac});}return log(_0x20c3c1(_0x468864._0x2984e1)+_0x4312f0[_0x20c3c1(0xd2)]+(_0x28c5d6?'\x20(season\x20'+_0x90f03+')':'')),_0x4312f0;});}function parseArchive(_0x30d8d5,_0x321d4a){var _0xdfa1a3={_0x43e5bc:0xf6};return __async(this,null,function*(){var _0x272776=_0x45eb,_0x3d3d6b=yield fetchText(_0x30d8d5,{'headers':{'Referer':MAIN_URL+'/'}},0x2ee0);if(!_0x3d3d6b)return[];var _0x22924d=[],_0x535471=/https?:\/\/hubcloud\.[a-z]+\/drive\/([a-z0-9_]+)/gi,_0x1aefbb;while((_0x1aefbb=_0x535471[_0x272776(0xd6)](_0x3d3d6b))!==null){var _0x47dacd=_0x1aefbb[0x0],_0x3602ad=_0x321d4a!=null;if(_0x3602ad){var _0x460f58=Math[_0x272776(0x10a)](0x0,_0x1aefbb['index']-0x12c),_0x122a86=_0x3d3d6b[_0x272776(_0xdfa1a3._0x43e5bc)](_0x460f58,_0x1aefbb['index']),_0xb60801=/(?:EP|Episode|E)\D*0*(\d+)/gi,_0x3a2a7b,_0x52f36e=-0x1;while((_0x3a2a7b=_0xb60801['exec'](_0x122a86))!==null){_0x52f36e=parseInt(_0x3a2a7b[0x1]);}if(_0x52f36e===-0x1||_0x52f36e!==_0x321d4a)continue;}_0x22924d[_0x272776(0xcb)]({'url':_0x47dacd,'id':_0x1aefbb[0x1]});}return log('archive\x20hosts:\x20'+_0x22924d['length']+(_0x3602ad?'\x20(ep\x20'+_0x321d4a+')':'')),_0x22924d;});}function minutes(){return String(new Date()['getMinutes']());}function decodeBase64(_0x284f74){var _0x502b70={_0x103641:0xe4},_0x1f7338=_0x14577e;if(typeof atob==='function')return atob(_0x284f74);var _0x24bbdb='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=',_0x3e4744='';_0x284f74=String(_0x284f74)[_0x1f7338(_0x502b70._0x103641)](/=+$/,'');for(var _0x42f884=0x0,_0x4efb32,_0x500a9a,_0x3c2313=0x0;_0x500a9a=_0x284f74['charAt'](_0x3c2313++);~_0x500a9a&&(_0x4efb32=_0x42f884%0x4?_0x4efb32*0x40+_0x500a9a:_0x500a9a,_0x42f884++%0x4)?_0x3e4744+=String['fromCharCode'](0xff&_0x4efb32>>(-0x2*_0x42f884&0x6)):0x0){_0x500a9a=_0x24bbdb[_0x1f7338(0xb5)](_0x500a9a);}return _0x3e4744;}function _0x40ed(){var _0x1cf878=['AgfZt3DUuhjVCgvYDhK','BwvZC2fNzq','mZi4mJyZndHcwKrVzKW','C3vIC3rYAw5N','ihn0CMvHBxm','ndi2mZC0ogHbAMjTta','BM8GAhvIy2XVDwqGAg9ZDhm','Bwf0y2G','mtaYmtqZodrSzKTnyMW','EwvHCG','CxvHBgL0Eq','AgvHzgvYCW','BM8GnZiWCc8XmdGWCc80AYbHCMnOAxzLCW','AgL0CW','mJe2mha','tw96AwXSys81lJaGkeXPBNv4oYbbBMrYB2LKide0oYbqAxHLBca4ifbYBYKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYnc4WlJaUmcbnB2jPBguGu2fMyxjPlZuZnY4ZnG','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','CMfUzg9T','zM9YrwfJAa','zw4TvvmSzw47Ct0WlJK','Aw5KzxG','ihr5Cgu9','ic0+ia','Bwf4','ndG2nJa5mfflB3LusW','C2vHCMnOigzVDw5Kia','CgvYBwfSAw5R','l3nLyxjJAc5WAha/Ct0','Aw5KzxHpzG','CMvSzwfZzv9KyxrL','Aw1KyG','Dg9mB3DLCKnHC2u','ifTt','zMv0y2G6ia','kdXOwZeTnL1BxJ5DkJ58phn0CM9Uz1TEpL0QpNW8C3bHBLTEpL0QpILBxhnCu117mcWXmdb9pYG/oLnLyxnVBNXtywLZB258u3rHzMzLBcLCCYOWkIHCzcSPxgiOpYfCCYPBlEkaKYSMxsK','Bg9N','jMfWCgvUzf90B19YzxnWB25Zzt1LEhrLCM5HBf9Pzhm','zgvMAw5LuhjVCgvYDgLLCW','zxH0zxjUywXFAwrZ','igH1yMnSB3vKigXPBMTZ','igu9','odeYq2HStfHw','zMf0ywW6ia','C2LNBMfS','Cg9ZDf90AxrSzq','zxHWB3j0CW','DhLWzq','mJa3mJK2uNvcsKX1','DMfSDwu','Aw1KyL9Pza','ChvZAa','mtHrBuzfyxC','mZq4owD0BvjfEG','vgLTzw91Dca','y2fSBa','DhzFCMvZDwX0CW','C2L6zq','BgvUz3rO','C29YDa','DgL0Bgu','igzVCJOG','zxHLyW','DhjPBq','mtq0mha','AhjLzG','mJiXmZC4nwjty3jPEG','Bw92Awu','CMfJzq','igfYy2HPDMuGBgLUA3m','DgHLBG','CMvXDwvZDdOGAwq9','kdXOwZeTnL1BxJ5DkJ58phn0CM9Uz1TEpL0QpIKUkJ8OpZPtzwfZB258u2fPC29UFfn0ywzMzwWPxhmQmcOOxgqRkvXZkLST4OctxvXZkJaQkfXKkYK','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','yxjJAgL2zsbSAw5RCZOG','ChjVDg90ExbL','CMvWBgfJzq','DgvZDa','zMLSDgvY','iIaO','C2vHCMnOihPLCM86ia','DxjS','zxjYB3i','C2vYAwvZ','zMLYC3rFywLYx2rHDgu','yxbWBhK','ig5VDcbMB3vUza','C3bSAxq','Ahr0Chm6lY9UzxC0lM1VDMLLC2rYAxzLCY5TEq','C2vHC29U','Ahr0Ca'];_0x40ed=function(){return _0x1cf878;};return _0x40ed();}function resolveHubcloud(_0x184abf,_0x31ef82,_0x259f83){var _0x38a1c6={_0xabb59e:0xfa,_0x1d580c:0xcb,_0x48c5fe:0xd2};return __async(this,null,function*(){var _0xbd1be1=_0x45eb,_0x52d277=yield fetchText(_0x184abf,{'headers':{'Cookie':'xla=s4t','Referer':ARCHIVE_DOMAIN+'/'}},0x2ee0);if(!_0x52d277)return[];var _0x50a18a=null,_0x8a7494=_0x52d277[_0xbd1be1(_0x38a1c6._0xabb59e)](/var\s+url\s*=\s*'([^']+)'/);if(_0x8a7494)_0x50a18a=_0x8a7494[0x1];if(!_0x50a18a){var _0x3084b0=_0x52d277['match'](/<a\s+id="download"\s+(?:x-href|href)="([^"]+)"/);if(_0x3084b0){_0x50a18a=_0x3084b0[0x1];if(!_0x50a18a['startsWith']('http'))try{_0x50a18a=decodeBase64(_0x50a18a);}catch(_0xe698cc){}}}if(!_0x50a18a)return[];var _0x4eaea8=yield fetchText(_0x50a18a,{'headers':{'Cookie':'xla=s4t','Referer':_0x184abf}},0x3a98);if(!_0x4eaea8)return[];var _0x3031a8=[],_0x5db87a,_0x38ab83=/href="(https?:\/\/fsl\.gigabytes\.icu[^"]+)"/gi;while((_0x5db87a=_0x38ab83[_0xbd1be1(0xd6)](_0x4eaea8))!==null){_0x3031a8[_0xbd1be1(_0x38a1c6._0x1d580c)]({'type':'FSLv2','url':_0x5db87a[0x1],'quality':_0x31ef82,'size':_0x259f83||''});}var _0x171b21=/href="(https?:\/\/(?:pub-[a-z0-9]+\.r2\.dev|[a-z0-9.]+\.buzz)[^"]+)"/gi;while((_0x5db87a=_0x171b21[_0xbd1be1(0xd6)](_0x4eaea8))!==null){_0x3031a8[_0xbd1be1(0xcb)]({'type':'FSL','url':_0x5db87a[0x1]+'1'+minutes(),'quality':_0x31ef82,'size':_0x259f83||''});}if(_0x3031a8[_0xbd1be1(_0x38a1c6._0x48c5fe)]===0x0){var _0x5c1a8a=_0x4eaea8['match'](/https?:\/\/[^\s"'<>]+\?token=\d+/);if(_0x5c1a8a){var _0x98a80=_0x5c1a8a[0x0][_0xbd1be1(0xe4)](/["'].*$/,'')['replace'](/[<>].*$/,'');_0x3031a8['push']({'type':'FSL','url':_0x98a80+'1'+minutes(),'quality':_0x31ef82,'size':_0x259f83||''});}}return _0x3031a8;});}function dedupe(_0x3e4d34){var _0x4fadb0={_0x3c0a32:0xe6},_0x417319=_0x14577e,_0x1910c0={};return(_0x3e4d34||[])[_0x417319(_0x4fadb0._0x3c0a32)](function(_0x3372dc){var _0x3cd45c=_0x417319;if(!_0x3372dc||!_0x3372dc['url']||_0x1910c0[_0x3372dc[_0x3cd45c(0xe9)]])return![];return _0x1910c0[_0x3372dc['url']]=!![],!![];});}function pad2(_0x351bee){return _0x351bee!=null&&_0x351bee<0xa?'0'+_0x351bee:String(_0x351bee);}function getStreams(_0x428d77,_0x4733d1,_0x530f9e,_0x52a8f7){var _0x332d37={_0x5b3b0a:0x108,_0x1a2136:0xc1,_0x469ef7:0xeb,_0x4e9d5f:0xb7,_0x3a0f4f:0xf2,_0x1708c2:0xd9,_0x51a976:0xd4,_0x46ae33:0xfc,_0x43e51a:0xd9,_0x4e8a4a:0xd9,_0x1d2287:0xff,_0x54b404:0xdd,_0x243be4:0x105,_0x56a8bf:0xd2,_0x13e1a8:0xd3,_0x2cef72:0xd2,_0x58f5ef:0xf7};return __async(this,null,function*(){var _0x3cc3e3={_0x1cafcd:0xb5},_0x115f39={_0x10a512:0xd1,_0x29c6b7:0xcb,_0x4ae8ec:0xc7},_0x1e4e2a={_0x19ad81:0xe9},_0x1d0b50=_0x45eb;try{log(_0x1d0b50(0xdf)+_0x428d77+_0x1d0b50(_0x332d37._0x5b3b0a)+_0x4733d1+'\x20s='+_0x530f9e+_0x1d0b50(_0x332d37._0x1a2136)+_0x52a8f7);var _0x3f994f=yield getMedia(_0x428d77,_0x4733d1);if(!_0x3f994f||!_0x3f994f['title'])return[];var _0x5f1f81=_0x4733d1==='tv'||_0x4733d1===_0x1d0b50(_0x332d37._0x469ef7),_0x44208c=_0x530f9e!=null?Number(_0x530f9e):null,_0x239f39=_0x52a8f7!=null?Number(_0x52a8f7):null;log('resolved:\x20\x22'+_0x3f994f[_0x1d0b50(0xd4)]+_0x1d0b50(0xe7)+(_0x3f994f['year']||'?')+')');var _0x4eb968,_0x4c40d6,_0x3d5682=null,_0x4aa93d=null;if(_0x3f994f['imdb']&&_0x3f994f[_0x1d0b50(_0x332d37._0x4e9d5f)][_0x1d0b50(0xb5)]('tt')===0x0){_0x4eb968=yield searchSite(_0x3f994f['imdb']);if(_0x5f1f81&&_0x44208c!=null)for(_0x4c40d6=0x0;_0x4c40d6<_0x4eb968['length'];_0x4c40d6++){if(_0x4eb968[_0x4c40d6]['imdb']!==_0x3f994f['imdb'])continue;var _0x54138b=_0x4eb968[_0x4c40d6]['href']['indexOf'](_0x1d0b50(_0x332d37._0x3a0f4f))===0x0?_0x4eb968[_0x4c40d6][_0x1d0b50(_0x332d37._0x1708c2)]:MAIN_URL+_0x4eb968[_0x4c40d6][_0x1d0b50(0xd9)],_0x5df7a8=yield fetchText(_0x54138b,{'headers':{'Referer':MAIN_URL+'/'}},0x2ee0);if(_0x5df7a8&&extractSeasonHtml(_0x5df7a8,_0x44208c)!==null){_0x3d5682=_0x4eb968[_0x4c40d6],_0x4aa93d=_0x5df7a8,log('imdb\x20season\x20match:\x20'+_0x3d5682[_0x1d0b50(_0x332d37._0x51a976)]);break;}}else for(_0x4c40d6=0x0;_0x4c40d6<_0x4eb968['length'];_0x4c40d6++){if(_0x4eb968[_0x4c40d6]['imdb']===_0x3f994f[_0x1d0b50(0xb7)]){_0x3d5682=_0x4eb968[_0x4c40d6],log('imdb\x20exact\x20match:\x20'+_0x3d5682['title']);break;}}}if(!_0x3d5682){_0x4eb968=yield searchSite(_0x3f994f[_0x1d0b50(0xd4)]);for(_0x4c40d6=0x0;_0x4c40d6<_0x4eb968[_0x1d0b50(0xd2)];_0x4c40d6++){if(isStrictMatch(_0x3f994f[_0x1d0b50(_0x332d37._0x51a976)],_0x3f994f[_0x1d0b50(_0x332d37._0x46ae33)],_0x4eb968[_0x4c40d6][_0x1d0b50(_0x332d37._0x51a976)],_0x4eb968[_0x4c40d6]['year'])){var _0x54138b=_0x4eb968[_0x4c40d6][_0x1d0b50(_0x332d37._0x43e51a)]['indexOf'](_0x1d0b50(_0x332d37._0x3a0f4f))===0x0?_0x4eb968[_0x4c40d6][_0x1d0b50(_0x332d37._0x1708c2)]:MAIN_URL+_0x4eb968[_0x4c40d6][_0x1d0b50(_0x332d37._0x4e8a4a)],_0x5df7a8=yield fetchText(_0x54138b,{'headers':{'Referer':MAIN_URL+'/'}},0x2ee0);if(!_0x5f1f81||extractSeasonHtml(_0x5df7a8,_0x44208c)!==null){_0x3d5682=_0x4eb968[_0x4c40d6],_0x4aa93d=_0x5df7a8,log('title\x20match:\x20'+_0x3d5682['title']);break;}}}}if(!_0x3d5682)return log('no\x20match'),[];if(!_0x4aa93d){var _0x57126d=_0x3d5682[_0x1d0b50(_0x332d37._0x43e51a)][_0x1d0b50(0xb5)]('http')===0x0?_0x3d5682['href']:MAIN_URL+_0x3d5682[_0x1d0b50(_0x332d37._0x1708c2)];_0x4aa93d=yield fetchText(_0x57126d,{'headers':{'Referer':MAIN_URL+'/'}},0x2ee0);if(!_0x4aa93d)return[];}var _0x10f531=extractSiteTitle(_0x4aa93d),_0x61f591='';_0x5f1f81&&(_0x61f591=(_0x10f531||_0x3f994f[_0x1d0b50(_0x332d37._0x51a976)])+_0x1d0b50(0xb9)+pad2(_0x44208c)+'E'+pad2(_0x239f39)+']');var _0x152044=yield parsePage(_0x3d5682[_0x1d0b50(_0x332d37._0x1708c2)][_0x1d0b50(0xb5)]('http')===0x0?_0x3d5682[_0x1d0b50(_0x332d37._0x1708c2)]:MAIN_URL+_0x3d5682[_0x1d0b50(0xd9)],_0x44208c,_0x4aa93d);_0x152044=_0x152044['filter'](function(_0x173f4b){return _0x173f4b['q']!=='480p';});if(_0x152044['length']===0x0)return log(_0x1d0b50(_0x332d37._0x1d2287)),[];log('processing\x20'+_0x152044[_0x1d0b50(0xd2)]+_0x1d0b50(_0x332d37._0x54b404));var _0xab2b4c=[];for(var _0x5ca29a=0x0;_0x5ca29a<_0x152044['length'];_0x5ca29a++){var _0x2aeba2=_0x152044[_0x5ca29a];try{var _0x3acfb3=yield parseArchive(_0x2aeba2['url'],_0x239f39);_0x3acfb3[_0x1d0b50(_0x332d37._0x243be4)](function(_0x23ce13){var _0x25e125=_0x1d0b50;_0xab2b4c[_0x25e125(0xcb)]({'url':_0x23ce13[_0x25e125(_0x1e4e2a._0x19ad81)],'q':_0x2aeba2['q'],'size':_0x2aeba2['size']});});}catch(_0x53a721){}}if(_0xab2b4c['length']===0x0)return log(_0x1d0b50(0xf9)),[];log('resolving\x20'+_0xab2b4c[_0x1d0b50(_0x332d37._0x56a8bf)]+_0x1d0b50(0xc0));var _0x41ca73=[];for(var _0x5ca29a=0x0;_0x5ca29a<_0xab2b4c['length'];_0x5ca29a++){var _0x5884b6=_0xab2b4c[_0x5ca29a];try{var _0x2bae5d=yield resolveHubcloud(_0x5884b6['url'],_0x5884b6['q'],_0x5884b6['size']);_0x41ca73['push'](_0x2bae5d);}catch(_0x3bed88){}}var _0x58db96=[];_0x41ca73['forEach'](function(_0x238992){_0x238992['forEach'](function(_0x3b6d5f){_0x58db96['push'](_0x3b6d5f);});});if(_0x58db96[_0x1d0b50(_0x332d37._0x56a8bf)]===0x0)return log('no\x20FSL\x20streams\x20resolved'),[];var _0xe2f76=_0x5f1f81&&_0x61f591?_0x61f591:_0x10f531,_0x4bf567=[];_0x58db96['forEach'](function(_0x292509){var _0x4f993b=_0x1d0b50,_0x5b4db8=_0x292509[_0x4f993b(_0x115f39._0x10a512)]?'\x20'+_0x292509[_0x4f993b(0xd1)]:'',_0x51f0ff=_0xe2f76+'\x20-\x20'+PROVIDER_NAME;_0x4bf567[_0x4f993b(_0x115f39._0x29c6b7)]({'name':_0x51f0ff,'title':'Auto','url':_0x292509['url'],'quality':_0x292509['quality'],'size':'('+_0x292509[_0x4f993b(_0x115f39._0x4ae8ec)]+')'+_0x5b4db8,'behaviorHints':{'notWebReady':!![],'proxyHeaders':{'request':{'Referer':ARCHIVE_DOMAIN+'/'}}}});}),_0x4bf567=dedupe(_0x4bf567);var _0x3e092a={'2160p':0x4,'1080p':0x3,'720p':0x2,'HD':0x1};return _0x4bf567[_0x1d0b50(_0x332d37._0x13e1a8)](function(_0xab5aee,_0x46debb){var _0x5be78f=_0x1d0b50,_0x272b8d=function(_0x3390f3){var _0x3ac0e9=_0x45eb;return _0x3390f3[_0x3ac0e9(_0x3cc3e3._0x1cafcd)]('(FSLv2)')!==-0x1?0x1:0x0;},_0x41a4d8=_0x272b8d(_0xab5aee['name']),_0x17af22=_0x272b8d(_0x46debb['name']);if(_0x41a4d8!==_0x17af22)return _0x17af22-_0x41a4d8;return(_0x3e092a[_0x46debb['quality']]||0x0)-(_0x3e092a[_0xab5aee[_0x5be78f(0xfd)]]||0x0);}),log('returning\x20'+_0x4bf567[_0x1d0b50(_0x332d37._0x2cef72)]+_0x1d0b50(_0x332d37._0x58f5ef)),_0x4bf567;}catch(_0x51244c){return err(_0x1d0b50(0xc3)+_0x51244c['message']),[];}});}typeof module!=='undefined'&&module['exports']?module[_0x14577e(0xc6)]={'getStreams':getStreams}:global['getStreams']=getStreams;



/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:7a60b5a9b638 */
;(function(g,c){"use strict";
var ASSET=/\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|otf|eot|json|xml|vtt|srt)(?:[?#]|$)/i;
var BADHOST=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|googletagmanager\.com|google-analytics\.com|doubleclick\.net)$/i;
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return""}}
function rejected(v){var h=host(v);return !/^https?:\/\//i.test(v)||!h||BADHOST.test(h)||ASSET.test(v)||/(?:trailer|bande-annonce|big[_-]?buck[_-]?bunny|sample[-_]?video|\/troll\/master\.m3u8)/i.test(v)}
function directByName(v){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/hls2?\//i.test(v)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function headers(row,referer,target){var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){if(String(k).toLowerCase()!=="range")out[k]=s(src[k])});if(referer&&!out.Referer&&!out.referer)out.Referer=referer;try{var o=new URL(referer||target).origin;if(o&&!out.Origin&&!out.origin)out.Origin=o}catch(_){}if(!directByName(target)&&!out.Range&&!out.range)out.Range="bytes=0-262143";return out}
function kindBytes(bytes){if(!bytes||bytes.length<4)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes[0]===71&&(bytes.length<189||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var x="";for(var i=0;i<Math.min(bytes.length,262144);i++)x+=String.fromCharCode(bytes[i]);return x}}
async function fetchResource(url,row,referer){try{var r=await g.fetch(url,{headers:headers(row,referer,url),redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buf=await r.arrayBuffer(),bytes=new Uint8Array(buf),text=decode(bytes.slice(0,300000));return{ok:!!r.ok,status:r.status,url:s(r.url||url),type:type,bytes:bytes,text:text,headers:headers(row,referer,r.url||url)}}catch(_){return null}}
function proof(r){if(!r||!r.ok)return null;var t=s(r.text).trimStart();if(t.indexOf("#EXTM3U")===0)return"hls";if(/<MPD[\s>]/i.test(t.slice(0,4096))||/application\/dash\+xml/i.test(r.type))return"dash";var b=kindBytes(r.bytes);if(b)return b;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;out.push(u)}var body=s(text),patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mpd|mp4|mkv|webm|embed|player|\/e\/|\/hls2?\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null){add(m[1]);if(out.length>=c.maxCandidates)return out}}return out}
async function resolve(url,row,referer,depth,seen){if(depth>c.maxDepth||rejected(url))return[];seen=seen||{};if(seen[url])return[];seen[url]=1;var r=await fetchResource(url,row,referer);if(!r)return[];var k=proof(r);if(k)return[{url:r.url||url,kind:k,headers:r.headers}];if(!/html|text|json|javascript|xml/i.test(r.type)&&!/[<>{}\[\]"']/.test(r.text||""))return[];var next=candidates(r.text,r.url||url),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var found=await resolve(next[i],row,r.url||url,depth+1,seen);for(var j=0;j<found.length;j++)if(!out.some(function(x){return x.url===found[j].url}))out.push(found[j])}return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function clone(row,media){var out=Object.assign({},row,{url:media.url,headers:media.headers||row.headers||{},isDirect:true,type:media.kind});return out}
async function enrich(list){var out=[],seen={};function add(row){var u=s(row&&row.url);if(!u||seen[u])return;seen[u]=1;out.push(row)}for(var i=0;i<list.length;i++){var row=list[i];if(!row||typeof row!=="object"){continue}var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u)){if(c.preserveOriginal)add(row);continue}if(i<c.maxRows&&!directByName(u)){var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||u),found=await resolve(u,row,ref,0,{});for(var j=0;j<found.length;j++)add(clone(row,found[j]))}add(row)}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalMediaEnrichmentV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var list=await enrich(x.list);return rebuild(v,x,list)};wrap.__nuvioGlobalMediaEnrichmentV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true});


/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:128b76741346 */
;(function(g,config){
  "use strict";
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function headerValue(stream,name){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var wanted=String(name||"").toLowerCase(),keys=Object.keys(src);
    for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===wanted)return clean(src[keys[i]]);
    return "";
  }
  function requestHeaders(stream,referer,range){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(out).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(out[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(out).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete out[k]});
        out.Referer=referer;try{out.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-4095";
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,text/plain,*/*";
    return out;
  }
  async function fetchBounded(url,stream,referer,range){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=setTimeout(function(){try{if(controller)controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream,referer,range),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      return {state:"ok",response:response,url:String(response.url||url),contentType:contentType};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{clearTimeout(timer)}
  }
  async function responseText(result){
    var response=result&&result.response;if(!response)return "";
    try{if(typeof response.text==="function")return clean(await response.text())}catch(_e){}
    try{if(typeof response.arrayBuffer==="function"){var ab=await response.arrayBuffer();return clean(new TextDecoder("utf-8").decode(ab))}}catch(_e){}
    try{if(response.body&&typeof response.body.getReader==="function"){var reader=response.body.getReader(),chunks=[],total=0;while(total<131072){var part=await reader.read();if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}if(!part||part.done)break}try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}var merged=new Uint8Array(total),offset=0;for(var i=0;i<chunks.length;i++){var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break}return clean(new TextDecoder("utf-8").decode(merged))}}catch(_e){}
    return "";
  }
  function playlistKind(body){
    var text=clean(body);if(!/^#EXTM3U(?:\s|$)/i.test(text))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(text))return "master";
    if(/#EXTINF\s*:/i.test(text)||/#EXT-X-PART\s*:/i.test(text)||/#EXT-X-MAP\s*:/i.test(text)){
      var lines=text.split(/\r?\n/).map(function(v){return v.trim()}).filter(Boolean);
      if(lines.some(function(v){return v.charAt(0)!=="#"}))return "media";
    }
    return "header_only";
  }
  function variantUris(body,base){
    var lines=clean(body).split(/\r?\n/),out=[];
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var candidate=clean(lines[j]);if(!candidate)continue;if(candidate.charAt(0)==="#")continue;
        var u=absolute(candidate,base);if(u&&out.indexOf(u)<0)out.push(u);break;
      }
      if(out.length>=config.maxChildren)break;
    }
    return out;
  }
  function audioUris(body,base){
    var out=[],lines=clean(body).split(/\r?\n/);
    lines.forEach(function(line){
      if(!/^#EXT-X-MEDIA\s*:/i.test(line)||!/TYPE\s*=\s*AUDIO/i.test(line))return;
      var m=line.match(/URI\s*=\s*"([^"]+)"/i)||line.match(/URI\s*=\s*([^,\s]+)/i);
      var u=m&&absolute(m[1],base);if(u&&out.indexOf(u)<0)out.push(u);
    });
    return out.slice(0,config.maxChildren);
  }
  async function validateChild(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);if(result.state!=="ok")return result.state;
    var body=await responseText(result),kind=playlistKind(body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function inspectHls(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,false);
    if(result.state!=="ok")return {state:result.state,reason:result.reason||"fetch_failed",result:result};
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return {state:"direct",format:ct.indexOf("webm")>=0?"webm":"mp4",url:result.url,result:result};
    var body=await responseText(result),kind=playlistKind(body);
    if(kind==="invalid"||kind==="header_only")return {state:"invalid",kind:kind,body:body,result:result};
    if(kind==="media")return {state:"valid",kind:kind,url:result.url,body:body,result:result};

    var variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);
    if(!variants.length)return {state:"invalid",kind:"master_without_variants",body:body,result:result};
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream,result.url||referer);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return {state:variantState,kind:"master_child_"+variantState,body:body,result:result};
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream,result.url||referer);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return {state:audioState,kind:"audio_child_"+audioState,body:body,result:result};
    }
    return {state:"valid",kind:"master",url:result.url,body:body,result:result};
  }
  function normalizedText(text){
    return clean(text).replace(/\\u002[fF]/g,"/").replace(/\\\//g,"/").replace(/&amp;/g,"&");
  }
  function candidateUrls(text,base){
    var body=normalizedText(text),out=[],seen={};
    function add(raw){
      var value=clean(raw).replace(/^['"]|['"]$/g,"");if(!value||/^javascript:|^data:/i.test(value))return;
      var u=absolute(value,base);if(!/^https?:\/\//i.test(u)||seen[u])return;seen[u]=1;out.push(u);
    }
    var patterns=[
      /(?:src|href|data-src|data-url|data-file|data-player|data-embed|file|source|url|playlist|hls|stream|embedUrl|embed_url)\s*[:=]\s*["']([^"']+)["']/gi,
      /(https?:\/\/[^"'<>\s\\]+)/gi,
      /["']([^"']+\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#][^"']*)?)["']/gi
    ],m;
    for(var i=0;i<patterns.length&&out.length<config.maxRecoveryCandidates;i++){
      patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null&&out.length<config.maxRecoveryCandidates)add(m[1]);
    }
    return out;
  }
  function mediaHint(url){return /\.m3u8(?:[?#]|$)|\/hls2?\//i.test(url)?"hls":/\.mpd(?:[?#]|$)/i.test(url)?"dash":/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(url)?"direct":"page"}
  function cloneRecovered(stream,url,format,referer){
    var row=Object.assign({},stream,{url:url}),headers={};
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};Object.keys(src).forEach(function(k){headers[k]=String(src[k])});
    if(referer){
      var refKey=Object.keys(headers).find(function(k){return k.toLowerCase()==="referer"}),currentRef=refKey?clean(headers[refKey]):"";
      if(!currentRef||currentRef!==clean(referer)){
        Object.keys(headers).forEach(function(k){var lower=k.toLowerCase();if(lower==="referer"||lower==="origin")delete headers[k]});
        headers.Referer=referer;try{headers.Origin=new URL(referer).origin}catch(_e){}
      }
    }
    if(Object.keys(headers).length)row.headers=headers;
    if(format==="hls"){row.type="hls";if("format" in row)row.format="m3u8"}
    else if(format==="dash"){row.type="dash";if("format" in row)row.format="mpd"}
    else if(format){row.type=format;if("format" in row)row.format=format}
    return row;
  }
  async function probeDirect(url,stream,referer){
    var result=await fetchBounded(url,stream,referer,true);if(result.state!=="ok")return null;
    var ct=result.contentType||"";
    if(/^video\//i.test(ct))return cloneRecovered(stream,result.url,ct.indexOf("webm")>=0?"webm":"mp4",referer);
    if(/(?:application\/dash\+xml|application\/xml|text\/xml)/i.test(ct)||/\.mpd(?:[?#]|$)/i.test(result.url)){
      var dash=await responseText(result);if(/<MPD(?:\s|>)/i.test(dash))return cloneRecovered(stream,result.url,"dash",referer);
    }
    if(/mpegurl/i.test(ct)||/\.m3u8(?:[?#]|$)/i.test(result.url)){
      var hls=await inspectHls(result.url,stream,referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||result.url,"hls",referer);
    }
    return null;
  }
  async function recover(stream,inspection){
    var queue=[],seen={},pages=0;
    function enqueue(url,referer){var u=absolute(url,referer||String(stream.url||""));if(!/^https?:\/\//i.test(u)||seen[u]||u===String(stream.url||""))return;seen[u]=1;queue.push({url:u,referer:referer||""})}
    var base=inspection&&inspection.result&&inspection.result.url||String(stream.url||"");
    candidateUrls(inspection&&inspection.body||"",base).forEach(function(u){enqueue(u,base)});
    var outerReferer=headerValue(stream,"referer");
    [stream&&stream.playerUrl,stream&&stream.embedUrl,stream&&stream.pageUrl,stream&&stream.sourceUrl,stream&&stream.referrer,stream&&stream.referer].forEach(function(u){if(u)enqueue(u,outerReferer||base)});
    if(outerReferer)enqueue(outerReferer,"");
    while(queue.length&&pages<config.maxRecoveryPages){
      var item=queue.shift(),kind=mediaHint(item.url);
      if(kind==="hls"){
        var hls=await inspectHls(item.url,stream,item.referer);if(hls.state==="valid")return cloneRecovered(stream,hls.url||item.url,"hls",item.referer);if(hls.state==="direct")return cloneRecovered(stream,hls.url||item.url,hls.format||"mp4",item.referer);
        candidateUrls(hls.body||"",hls.result&&hls.result.url||item.url).forEach(function(u){enqueue(u,hls.result&&hls.result.url||item.url)});continue;
      }
      if(kind==="direct"||kind==="dash"){
        var direct=await probeDirect(item.url,stream,item.referer);if(direct)return direct;continue;
      }
      pages++;
      var page=await fetchBounded(item.url,stream,item.referer,false);if(page.state!=="ok")continue;
      var ct=page.contentType||"";
      if(/^video\//i.test(ct))return cloneRecovered(stream,page.url,ct.indexOf("webm")>=0?"webm":"mp4",item.referer);
      var body=await responseText(page);
      if(/^#EXTM3U(?:\s|$)/i.test(body)){
        var pageHls=await inspectHls(page.url,stream,item.referer);if(pageHls.state==="valid")return cloneRecovered(stream,pageHls.url||page.url,"hls",item.referer);
      }
      if(/<MPD(?:\s|>)/i.test(body))return cloneRecovered(stream,page.url,"dash",item.referer);
      candidateUrls(body,page.url||item.url).forEach(function(u){enqueue(u,page.url||item.url)});
    }
    return null;
  }
  async function validateOrRecover(stream){
    var inspection=await inspectHls(String(stream.url||""),stream,headerValue(stream,"referer"));
    if(inspection.state==="valid"||inspection.state==="unknown")return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!hlsHint(stream))return stream;
      var output=await validateOrRecover(stream);
      if(!output){
        try{console.warn("[Nuvio HLS integrity] rejected malformed playlist after bounded recovery",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
      }
      return output;
    }));
    var filtered=checks.filter(Boolean);
    if(Array.isArray(value))return filtered;
    var copy=Object.assign({},value);copy.streams=filtered;return copy;
  }
  function wrap(target,key){
    if(!target||typeof target[key]!=="function"||target[key].__nuvioHlsIntegrityV1)return false;
    var native=target[key];
    var wrapped=async function(){return filterRows(await native.apply(this,arguments))};
    try{Object.defineProperty(wrapped,"__nuvioHlsIntegrityV1",{value:true})}catch(_e){wrapped.__nuvioHlsIntegrityV1=true}
    target[key]=wrapped;return true;
  }
  function install(){
    var done=false;
    try{done=wrap(g,"getStreams")||done}catch(_e){}
    try{if(typeof module!=="undefined"&&module&&module.exports){done=wrap(module.exports,"getStreams")||done;done=wrap(module.exports,"streams")||done}}catch(_e){}
    try{if(typeof exports!=="undefined")done=wrap(exports,"getStreams")||done}catch(_e){}
    return done;
  }
  install();
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2,"maxRecoveryPages":4,"maxRecoveryCandidates":12,"implementationRevision":"recovery-first-v3"});
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:a719f196c9a2 */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{id:first,mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};var raw=s(q.tmdbId||q.tmdb_id||q.imdbId||q.imdb_id||q.id||first),m;q.mediaType=s(q.mediaType||q.type||q.category||"movie").toLowerCase();q.season=Number(q.season)||0;q.episode=Number(q.episode)||0;q.tmdbId="";q.imdbId="";m=/^(?:imdb:)?(tt\d+)(?::(\d+):(?:(\d+)))?$/i.exec(raw);if(m){q.imdbId=m[1].toLowerCase();if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}else{raw=raw.replace(/^tmdb:/i,"");m=/^(\d+)(?::(\d+):(?:(\d+)))?$/.exec(raw);if(m){q.tmdbId=m[1];if(!q.season&&m[2])q.season=Number(m[2])||0;if(!q.episode&&m[3])q.episode=Number(m[3])||0}}return q}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function request(url,json,referer){try{var h={Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(referer){h.Referer=referer;try{h.Origin=new URL(referer).origin}catch(_){}}var r=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});if(!r||!r.ok)return null;return{url:s(r.url||url),body:json?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
function kindFor(q){if(q.mediaType==="tv")return"tv";if(q.mediaType==="anime"&&q.season&&q.episode)return"tv";return"movie"}
async function resolveIdentity(q,kind){if(/^\d+$/.test(q.tmdbId||""))return{tmdbId:q.tmdbId,imdbId:q.imdbId||"",seed:null};if(!/^tt\d+$/i.test(q.imdbId||""))return{tmdbId:"",imdbId:q.imdbId||"",seed:null};var r=await request("https://api.themoviedb.org/3/find/"+encodeURIComponent(q.imdbId)+"?api_key="+TMDB_KEY+"&external_source=imdb_id",true);if(!r||!r.body)return{tmdbId:"",imdbId:q.imdbId,seed:null};var preferred=kind==="tv"?(r.body.tv_results||[]):(r.body.movie_results||[]),other=kind==="tv"?(r.body.movie_results||[]):(r.body.tv_results||[]),seed=(preferred[0]||other[0]||null);return{tmdbId:seed&&seed.id?String(seed.id):"",imdbId:q.imdbId,seed:seed}}
async function meta(q){var titles=unique([q.title,q.name,q.label,q.settings&&q.settings.title]),year=Number(q.year||q.settings&&q.settings.year)||0,kind=kindFor(q),identity=await resolveIdentity(q,kind);if(identity.seed){var sd=identity.seed;titles=unique(titles.concat([sd.title,sd.name,sd.original_title,sd.original_name]));var seedDate=s(sd.release_date||sd.first_air_date);year=year||Number(seedDate.slice(0,4))||0}if(identity.tmdbId){var urls=["https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"?api_key="+TMDB_KEY+"&language=en-US"];for(var i=0;i<urls.length;i++){var r=await request(urls[i],true);if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);year=year||Number(date.slice(0,4))||0}}var alt=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(identity.tmdbId)+"/alternative_titles?api_key="+TMDB_KEY,true);if(alt&&alt.body){var rows=alt.body.titles||alt.body.results||[],priority={FR:100,US:90,GB:80,CA:70,DK:60};rows=rows.slice().sort(function(a,b){return(priority[String(b&&b.iso_3166_1||"").toUpperCase()]||0)-(priority[String(a&&a.iso_3166_1||"").toUpperCase()]||0)});rows.slice(0,50).forEach(function(x){if(x&&x.title)titles.push(x.title)});titles=unique(titles)}}return{titles:titles.slice(0,c.maxAliases),year:year,tmdbId:identity.tmdbId,imdbId:identity.imdbId}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,streaming:1,watch:1,voir:1,regarder:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function aliasScore(text,m){var n=norm(text),best=-1;(m.titles||[]).forEach(function(t){var nt=norm(t),want=tokens(t);if(!want.length)return;var score=n.indexOf(nt)>=0?120:0;if(!score&&want.every(function(x){return n.indexOf(x)>=0}))score=90;if(score>best)best=score});if(best<0)return-1;var years=n.match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&years.indexOf(String(m.year))<0)return-1;if(m.year&&n.indexOf(String(m.year))>=0)best+=15;return best}
function links(html,base,m){var rows=[],seen={},re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(String(html||"")))!==null){var u=abs(x[2],base),label=s(x[1])+" "+s(x[3])+" "+s(x[4]).replace(/<[^>]+>/g," ");if(!u||seen[u])continue;seen[u]=1;var score=aliasScore(label+" "+u,m);if(score>=90)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).slice(0,c.maxCandidates)}
function mediaish(u){return/(?:\.m3u8|\.mpd|\.mp4|\.mkv|\.webm)(?:[?#]|$)|\/(?:embed|player|watch|stream|video)(?:[/?#.-]|$)|\/e\//i.test(u)}
function extractPlayers(html,base,q){var text=String(html||"").replace(/\\\//g,"/"),out=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u]||!/^https?:\/\//i.test(u)||!mediaish(u))return;seen[u]=1;out.push(u)}var scoped=text;if((q.mediaType==="tv"||q.mediaType==="anime")&&q.season&&q.episode){var patterns=[new RegExp("s(?:aison|eason)?[ ._-]*0?"+q.season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+q.episode,"i"),new RegExp("(?:episode|ep)[ ._-]*0?"+q.episode,"i")],chunks=text.split(/(?=<[^>]+(?:episode|season|saison|data-ep))/i).filter(function(x){return patterns.some(function(p){return p.test(x)})});if(chunks.length)scoped=chunks.join("\n");else return[]}var patterns2=[/(?:src|href|data-src|data-url|data-embed|data-player|data-video|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi],m;for(var i=0;i<patterns2.length;i++){patterns2[i].lastIndex=0;while((m=patterns2[i].exec(scoped))!==null){add(m[1]);if(out.length>=c.maxPlayers)return out}}return out}
function rows(urls,m,page){return urls.slice(0,c.maxPlayers).map(function(u,i){var out={name:c.providerName+(urls.length>1?" #"+(i+1):""),title:c.providerName+" - "+(m.titles[0]||"Media"),url:u,quality:"Unknown",headers:{Referer:page,Origin:(function(){try{return new URL(page).origin}catch(_){return c.baseUrl}})()}};if(c.languageHint)out.language=c.languageHint;if(/\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(u))out.isDirect=true;return out})}
function idEvidence(body,m){var text=String(body||"");if(m.tmdbId&&new RegExp("tmdb[^0-9]{0,24}"+String(m.tmdbId),"i").test(text))return true;if(m.imdbId&&new RegExp("imdb[^a-z0-9]{0,24}"+String(m.imdbId),"i").test(text))return true;return false}
async function recover(q,knownMeta,deadline){if(["movie","tv","anime"].indexOf(q.mediaType)<0||Date.now()>=deadline)return[];var m=knownMeta||await meta(q);if(!m.titles.length||Date.now()>=deadline)return[];var guessed=[],found=[],searches=[];m.titles.forEach(function(t){guessed.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&found.length<c.maxCandidates*4&&Date.now()<deadline;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)found=found.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}var candidates=unique(found.concat(guessed)).slice(0,c.maxCandidates);for(var j=0;j<candidates.length&&Date.now()<deadline;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!idEvidence(page.body,m))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function identityLabel(row){var label=s(row&&((row.title||row.description||row.filename||row.name)||"")),base="";try{base=decodeURIComponent(new URL(s(row&&row.url)).pathname.split("/").filter(Boolean).pop()||"").replace(/\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)$/i,"")}catch(_){}var human=tokens(base).filter(function(x){return/^[a-z]{3,}$/i.test(x)});return label+(human.length>=2?" "+base:"")}
function nativeIdentityReject(row,q,m){var label=identityLabel(row);if(!label)return false;var se=/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(label)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(label);if(q.mediaType==="movie"&&se)return true;if(se&&(q.mediaType==="tv"||q.mediaType==="anime")){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true}if(aliasScore(label,m)>=90)return false;var tech={server:1,serveur:1,stream:1,streaming:1,source:1,mirror:1,direct:1,download:1,telecharger:1,play:1,player:1,vcloud:1,hubcloud:1,file:1,video:1,quality:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var providerTokens=tokens(c.providerName),expected={};(m.titles||[]).forEach(function(t){tokens(t).forEach(function(x){expected[x]=1})});var words=tokens(label).filter(function(x){return !tech[x]&&providerTokens.indexOf(x)<0&&!/^\d{3,4}p$/.test(x)});if(words.length<2)return false;for(var i=0;i<words.length;i++)if(expected[words[i]])return false;return true}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var q=args(arguments),v,deadline=Date.now()+c.budgetMs;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v),m=null;if(x&&x.list.length){try{m=await meta(q)}catch(_){m=null}if(!m||!m.titles||!m.titles.length)return v;var kept=x.list.filter(function(row){return !nativeIdentityReject(row,q,m)});if(kept.length)return rebuild(v,x,kept)}var recovered=await recover(q,m,deadline);if(!recovered.length)return x?rebuild(v,x,[]):v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://new2.moviesdrive.christmas","providerName":"moviesdrive","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"budgetMs":45000,"languageHint":"","implementationRevision":"native-media-filename-identity-v3"});
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:c236a483d58e */
;(function(g,c){
  "use strict";
  function s(v){return String(v==null?"":v).trim()}
  function slot(v){
    if(Array.isArray(v))return {key:null,list:v};
    if(v&&typeof v==="object"){
      for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return {key:k,list:v[k]}}
    }
    return null;
  }
  function rebuild(v,x,list){
    if(x.key===null)return list;
    var o=Object.assign({},v);o[x.key]=list;return o;
  }
  function req(a){
    var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{
      tmdbId:first,mediaType:a[1],season:a[2],episode:a[3]
    };
    q.tmdbId=s(q.tmdbId||q.id||first).replace(/^tmdb:/i,"").split(":")[0];
    q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();
    q.season=Number(q.season||a[2]||0)||0;
    q.episode=Number(q.episode||a[3]||0)||0;
    return q;
  }
  function isTv(){
    try{
      if(typeof g.__native_fetch==="function")return true;
      var ua=s(g.navigator&&g.navigator.userAgent);
      return /NuvioTV|Android TV/i.test(ua);
    }catch(_e){return false}
  }
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{
      if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms);
    }catch(_e){}
    return void 0;
  }
  async function responseText(r){
    if(!r)return "";
    try{if(typeof r.text==="function")return s(await r.text())}catch(_e){}
    try{
      if(typeof r.arrayBuffer==="function"){
        var ab=await r.arrayBuffer();
        if(ab){
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(new Uint8Array(ab)));
          if(typeof Buffer!=="undefined")return s(Buffer.from(ab).toString("utf8"));
        }
      }
    }catch(_e){}
    try{
      if(r.body&&typeof r.body.getReader==="function"){
        var reader=r.body.getReader(),chunks=[],total=0;
        while(total<262144){
          var part=await reader.read();
          if(part&&part.value){chunks.push(part.value);total+=part.value.byteLength||part.value.length||0}
          if(!part||part.done)break;
          if(total>0)break;
        }
        try{if(typeof reader.cancel==="function")await reader.cancel()}catch(_e){}
        if(total){
          var merged=new Uint8Array(total),offset=0;
          for(var i=0;i<chunks.length;i++){
            var value=chunks[i],take=Math.min(value.byteLength||value.length||0,total-offset);
            merged.set(value.subarray?value.subarray(0,take):value,offset);offset+=take;if(offset>=total)break;
          }
          if(typeof TextDecoder!=="undefined")return s(new TextDecoder("utf-8").decode(merged));
          if(typeof Buffer!=="undefined")return s(Buffer.from(merged).toString("utf8"));
        }
      }
    }catch(_e){}
    return "";
  }
  async function fetchText(url,row,range){
    try{
      var r=await g.fetch(url,{method:"GET",redirect:"follow",headers:headers(row,range),signal:timeoutSignal(c.timeoutMs)});
      if(!r)return {state:"unknown",reason:"no_response"};
      var st=Number(r.status||0),ct=s(r.headers&&r.headers.get?r.headers.get("content-type"):"").toLowerCase();
      if(st===401||st===403||st===404||st===410||st>=500)return {state:"dead",status:st,contentType:ct};
      if(!r.ok)return {state:"unknown",status:st,contentType:ct};
      var text=await responseText(r);
      return {state:"ok",status:st,url:s(r.url||url),contentType:ct,text:text};
    }catch(e){
      return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"};
    }
  }
  function playlistKind(text){
    var body=s(text).replace(/^\uFEFF/,"");
    if(!/^#EXTM3U(?:\s|$)/i.test(body))return "invalid";
    if(/#EXT-X-STREAM-INF\s*:/i.test(body))return "master";
    if(/#EXTINF\s*:/i.test(body))return "media";
    return "unknown";
  }
  function firstVariant(text,base){
    var lines=s(text).split(/\r?\n/);
    for(var i=0;i<lines.length;i++){
      if(!/^#EXT-X-STREAM-INF\s*:/i.test(lines[i]))continue;
      for(var j=i+1;j<lines.length;j++){
        var v=s(lines[j]);if(!v||v.charAt(0)==="#")continue;
        try{return new URL(v,base).toString()}catch(_e){return ""}
      }
    }
    return "";
  }
  function durationSeconds(text){
    var total=0,count=0,re=/#EXTINF\s*:\s*([0-9]+(?:\.[0-9]+)?)/gi,m;
    while((m=re.exec(s(text)))!==null){var n=Number(m[1]);if(Number.isFinite(n)&&n>0){total+=n;count++}}
    if(count<2||total<60)return null;
    return total;
  }
  async function inspectHls(row,url){
    var r=await fetchText(url,row,false);
    if(r.state!=="ok")return r;
    var kind=playlistKind(r.text);
    if(kind==="invalid")return {state:"dead",reason:"not_hls",status:r.status};
    if(kind==="media")return {state:"ok",duration:durationSeconds(r.text),url:r.url||url};
    if(kind==="master"){
      var child=firstVariant(r.text,r.url||url);
      if(!child)return {state:"dead",reason:"master_without_variant"};
      var cr=await fetchText(child,row,false);
      if(cr.state!=="ok")return cr;
      var ck=playlistKind(cr.text);
      if(ck!=="media"&&ck!=="master")return {state:"dead",reason:"invalid_child"};
      return {state:"ok",duration:durationSeconds(cr.text),url:r.url||url};
    }
    return {state:"ok",duration:null,url:r.url||url};
  }
  function mediaKind(row){
    var u=s(row&&row.url).toLowerCase(),t=s(row&&(row.type||row.format)).toLowerCase();
    if(/\.m3u8(?:[?#]|$)|\/hls2?\//i.test(u)||/hls|mpegurl|m3u8/.test(t))return "hls";
    if(/\.(?:mp4|mkv|webm)(?:[?#]|$)/i.test(u)||/mp4|matroska|webm|video\//.test(t))return "direct";
    return "other";
  }
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie";
    var url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else{
      url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
    }
    try{
      var r=await g.fetch(url,{headers:{Accept:"application/json"},signal:timeoutSignal(c.tmdbTimeoutMs)});
      if(!r||!r.ok)return null;
      var d=await r.json(),minutes=Number(d&&d.runtime||0);
      if(!minutes&&kind==="tv"&&Array.isArray(d&&d.episode_run_time)&&d.episode_run_time.length)minutes=Number(d.episode_run_time[0]||0);
      return minutes>=5?minutes*60:null;
    }catch(_e){return null}
  }
  async function directPlayable(row,url){
    var r=await fetchText(url,row,true);
    if(r.state!=="ok")return r;
    if(/text\/html|application\/xhtml/i.test(r.contentType)||/^<!doctype html|^<html/i.test(r.text||""))return {state:"dead",reason:"html_payload"};
    return {state:"ok"};
  }
  async function check(row,expected,tv){
    if(!row||typeof row!=="object"||!/^https?:\/\//i.test(s(row.url)))return {keep:true};
    var kind=mediaKind(row),result;
    if(kind==="hls")result=await inspectHls(row,s(row.url));
    else if(kind==="direct")result=await directPlayable(row,s(row.url));
    else return {keep:true};
    if(result.state==="dead")return {keep:false,reason:result.reason||("http_"+result.status)};
    if(result.state==="unknown"){
      if(c.strictPlayback||tv)return {keep:false,reason:result.reason||"unverified_media"};
      return {keep:true};
    }
    if(kind==="hls"&&expected&&result.duration){
      var ratio=result.duration/expected;
      if(ratio<c.minDurationRatio||ratio>c.maxDurationRatio)return {keep:false,reason:"duration_identity_mismatch",ratio:ratio};
    }
    return {keep:true};
  }
  function install(o,k){
    if(!o||typeof o[k]!=="function"||o[k].__nuvioRuntimeMediaSafetyV1)return false;
    var native=o[k];
    var wrap=async function(){
      var v=await native.apply(this,arguments),x=slot(v);
      if(!x||!x.list.length)return v;
      var q=req(arguments),tv=isTv(),expected=await expectedSeconds(q);
      var head=x.list.slice(0,c.maxRows),tail=x.list.slice(c.maxRows);
      var checks=await Promise.all(head.map(function(row){return check(row,expected,tv)}));
      var kept=head.filter(function(_row,i){return checks[i]&&checks[i].keep}).concat(tail);
      return rebuild(v,x,kept);
    };
    wrap.__nuvioRuntimeMediaSafetyV1=true;o[k]=wrap;return true;
  }
  var ok=false;
  try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_e){}
  try{
    if(g&&typeof g.getStreams==="function"){
      if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;
      else install(g,"getStreams");
    }
  }catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"moviesdrive","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"field-safety-v2"});
