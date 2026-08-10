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
})(typeof globalThis!=="undefined"?globalThis:this,[["YXBpLnRvZmxpeC5zaXRl","api.tfx05.lol"],["dG9mbGl4LnNpdGU=","tfx05.lol"]]);
var _0x1d62d1=_0x4e7c;(function(_0x30cb58,_0x953a40){var _0x753ca8={_0xabf93e:0xae,_0x55aa7c:0xbc,_0x1da6d0:0xb2,_0x22c1a3:0x89,_0x582fde:0x75,_0xa1183a:0x9a,_0x4b2530:0xb5},_0x3e2c0e=_0x4e7c,_0x35a85a=_0x30cb58();while(!![]){try{var _0x302221=parseInt(_0x3e2c0e(_0x753ca8._0xabf93e))/0x1*(-parseInt(_0x3e2c0e(0xac))/0x2)+-parseInt(_0x3e2c0e(0x80))/0x3*(-parseInt(_0x3e2c0e(_0x753ca8._0x55aa7c))/0x4)+-parseInt(_0x3e2c0e(0x7b))/0x5+parseInt(_0x3e2c0e(_0x753ca8._0x1da6d0))/0x6+parseInt(_0x3e2c0e(_0x753ca8._0x22c1a3))/0x7+parseInt(_0x3e2c0e(_0x753ca8._0x582fde))/0x8*(parseInt(_0x3e2c0e(_0x753ca8._0xa1183a))/0x9)+-parseInt(_0x3e2c0e(_0x753ca8._0x4b2530))/0xa;if(_0x302221===_0x953a40)break;else _0x35a85a['push'](_0x35a85a['shift']());}catch(_0x58e41e){_0x35a85a['push'](_0x35a85a['shift']());}}}(_0x5a41,0x8c3b1));var DOMAINS_URL=_0x1d62d1(0x81),TOFLIX_FALLBACK=_0x1d62d1(0x9f),TOFLIX_API=_0x1d62d1(0xa9)+TOFLIX_FALLBACK+'/toflix_api.php',TOFLIX_REFERER=_0x1d62d1(0x8a)+TOFLIX_FALLBACK+'/',TOFLIX_TOKEN=_0x1d62d1(0xb6),ZEUS_BASE='https://apis.wavewatch.xyz/zeus.php',ZEUS_REFERER=_0x1d62d1(0x8a)+TOFLIX_FALLBACK+'/',_cachedEndpoint=null;function _0x5a41(){var _0x483927=['C2L0zq','DxjS','Bg9N','C291CMnLCW','w1rVrMXPEf0Gzg9TywLUCY5QC29UimoPy2HVDCoPlcbMywXSyMfJAZOGDg9MBgL4lG','zMfZDgzSDxG','Bwf0y2G','C2vYAwuVzMfZDgzSDxHFzxbPC29Kzxm','ic0GvKy','ChvZAa','Ahr0Chm6lY9HCgKUDg9MBgL4lG','wMv1CZOGyxvJDw5LihnVDxjJzsbKAxjLy3rL','DgHLBG','odC1ogTuz2zKAa','ig5VBIb0CM91DMuGzw4GrMfZDezSDxG','mtjnyKziBKG','ywXS','BMfRAw9ZlMfYDa','vg9gBgL4ia','mJyYotm3ne1XuvrKvW','qxvJDw5LihnVDxjJzsbKAxnWB25PyMXL','zxzLBNq6','mJmWndu4mZbKtMfus00','vg9IAunVy29uB2zSAxGYmdi1vg9Rzw5ezuXHvJjnzwLSBgv1CLnPDgvezvn0CMvHBwLUqxvnB25KzuvUDgLLCLf1AuvJCMfZzvrVDxrtDxjtB25dAgvTAw5ozurLDMvUzxPqyxnkywXVDxHcyw5KzurLtM9VyNm','Bxa0','BgvUz3rO','zgf0ytO','l3rVzMXPEf9HCgKUCgHW','AwzYyw1L','nhrbu2TRwa','rxbPC29Kzsbt','jNm9','mJriDuDvDeu','DgL0Bgu','C2vHC29UCW','C291CMnL','DhjPBq','C3bSAxq','mtmXodC3nxfTthjwuW','y2f0y2G','EMv1CW','C3rHDhvZ','y2HHCKf0','mJKWnti4munwD3DpBa','Ahr0Chm6lY9YyxCUz2L0AhvIDxnLCMnVBNrLBNqUy29Tl3DVB29KEwHVB2qVBNv2Aw8TCMvWBY9TywLUl2rVBwfPBNmUANnVBG','C3rYAw5NAwz5','yxbWBgLJyxrPB24VANnVBG','CMvWBgfJzq','BwvZC2fNzq','BMfTzq','p3nZzsz0ExbLpxr2jMLKpq','qujdrevgr0HjsKTmtu5puffsu1rvvLDywvPHyMnKzwzNAgLQA2XTBM9WCxjZDhv2D3H5EJaXmJm0nty3odKRlZ0','ntKXotiYohDZrxboqG','Ahr0Chm6lY90B2zSAxGU','ANnVBG','ChjVDMLKzxi','Ahr0Ca','zNjVBunOyxjdB2rL','Dg9vChbLCKnHC2u','Aw5KzxHpzG','yxbP','y29Uy2f0','Dg9MBgL4','Btn1oa','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2','vg9gBgL4','rMLSBsbUB24GzgLZCg9UAwjSzq','sfruuca','wMv1CYbivfrqia','mJGYotaZm3zoqNDYDq','p3nZzsz0ExbLpw1VDMLLjMLKpq','ig5VBIbKAxnWB25PyMXL','CMvMzxjLCG','ic0G'];_0x5a41=function(){return _0x483927;};return _0x5a41();}function detectToflixEndpoint(){/* NUVIO_TOFLIX_OFFICIAL_ENDPOINT_V1 */
var site='https://tfx05.lol',fallbackApi='https://api.tfx05.lol/toflix_api.php';
if(_cachedEndpoint)return Promise.resolve(_cachedEndpoint);
return fetch(site+"/",{headers:{"Accept":"text/html,*/*;q=0.8"}}).then(function(response){
  if(!response||!response.ok)throw new Error("ToFlix terminal site HTTP "+(response&&response.status));
  var finalSite=response.url||site+"/";
  return response.text().then(function(body){return {body:body,site:new URL(finalSite).origin}});
}).then(function(result){
  var decoded=String(result.body||"").split("\\/").join("/");
  var match=decoded.match(/https?:\/\/[^\s<>]+\/toflix_api\.php(?:\?[^\s<>]+)?/i);
  var api=match?match[0]:fallbackApi;
  var referer=result.site.endsWith("/")?result.site:result.site+"/";
  _cachedEndpoint={api:api,referer:referer,zeusReferer:referer,zeus_referer:referer};
  return _cachedEndpoint;
}).catch(function(error){
  console.warn("[ToFlix] terminal bootstrap failed, using validated fallback:",error&&error.message||error);
  var referer=site+"/";
  return {api:fallbackApi,referer:referer,zeusReferer:referer,zeus_referer:referer};
});
}function _0x4e7c(_0xcad861,_0x402701){_0xcad861=_0xcad861-0x75;var _0x5a410e=_0x5a41();var _0x4e7c98=_0x5a410e[_0xcad861];if(_0x4e7c['aamdGV']===undefined){var _0x6062d6=function(_0x56a5c1){var _0x4a804f='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';var _0x48b069='',_0x135b34='';for(var _0x1298c8=0x0,_0x322dc0,_0x3f41f5,_0x594321=0x0;_0x3f41f5=_0x56a5c1['charAt'](_0x594321++);~_0x3f41f5&&(_0x322dc0=_0x1298c8%0x4?_0x322dc0*0x40+_0x3f41f5:_0x3f41f5,_0x1298c8++%0x4)?_0x48b069+=String['fromCharCode'](0xff&_0x322dc0>>(-0x2*_0x1298c8&0x6)):0x0){_0x3f41f5=_0x4a804f['indexOf'](_0x3f41f5);}for(var _0x44711f=0x0,_0x5080d1=_0x48b069['length'];_0x44711f<_0x5080d1;_0x44711f++){_0x135b34+='%'+('00'+_0x48b069['charCodeAt'](_0x44711f)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x135b34);};_0x4e7c['oSJwDV']=_0x6062d6,_0x4e7c['sVyLEP']={},_0x4e7c['aamdGV']=!![];}var _0x52d8f4=_0x5a410e[0x0],_0x1421da=_0xcad861+_0x52d8f4,_0x3ad650=_0x4e7c['sVyLEP'][_0x1421da];return!_0x3ad650?(_0x4e7c98=_0x4e7c['oSJwDV'](_0x4e7c98),_0x4e7c['sVyLEP'][_0x1421da]=_0x4e7c98):_0x4e7c98=_0x3ad650,_0x4e7c98;}function callApi(_0x322dc0,_0x3f41f5,_0x594321){var _0x5f650e={_0x4f068b:0x83,_0x20175f:0x82},_0x2cf4a4={_0x1cc868:0x8b},_0x423d31=_0x1d62d1;return fetch(_0x322dc0,{'method':'POST','headers':{'Content-Type':_0x423d31(_0x5f650e._0x4f068b),'tfxtoken':TOFLIX_TOKEN,'Origin':_0x3f41f5[_0x423d31(0x84)](/\/$/,''),'Referer':_0x3f41f5},'body':JSON[_0x423d31(_0x5f650e._0x20175f)](_0x594321)})['then'](function(_0x44711f){var _0x61cab9=_0x423d31;if(!_0x44711f['ok'])throw new Error('HTTP\x20'+_0x44711f[_0x61cab9(0x7e)]);return _0x44711f[_0x61cab9(_0x2cf4a4._0x1cc868)]();});}function b64decode(_0x5080d1){var _0x4feda1={_0x791442:0x88,_0x19ee82:0x7f,_0x263df1:0x7f,_0x4ca909:0x8e,_0x2e53b4:0x8e},_0x558a71=_0x1d62d1,_0x5efee9=_0x558a71(_0x4feda1._0x791442),_0x4eb3ff='';_0x5080d1=_0x5080d1['replace'](/[^A-Za-z0-9+/=]/g,'');for(var _0x178b4c=0x0;_0x178b4c<_0x5080d1[_0x558a71(0xb8)];){var _0x26ce36=_0x5efee9['indexOf'](_0x5080d1[_0x558a71(0x7f)](_0x178b4c++)),_0x226537=_0x5efee9['indexOf'](_0x5080d1[_0x558a71(_0x4feda1._0x19ee82)](_0x178b4c++)),_0x113c77=_0x5efee9[_0x558a71(0x90)](_0x5080d1[_0x558a71(_0x4feda1._0x263df1)](_0x178b4c++)),_0x4c6bc0=_0x5efee9['indexOf'](_0x5080d1[_0x558a71(_0x4feda1._0x263df1)](_0x178b4c++)),_0x3e7ad8=_0x26ce36<<0x2|_0x226537>>0x4,_0x543c04=(_0x226537&0xf)<<0x4|_0x113c77>>0x2,_0x4d3bd5=(_0x113c77&0x3)<<0x6|_0x4c6bc0;_0x4eb3ff+=String[_0x558a71(_0x4feda1._0x4ca909)](_0x3e7ad8);if(_0x113c77!==0x40)_0x4eb3ff+=String[_0x558a71(_0x4feda1._0x2e53b4)](_0x543c04);if(_0x4c6bc0!==0x40)_0x4eb3ff+=String['fromCharCode'](_0x4d3bd5);}return _0x4eb3ff['replace'](/[^\x20-\x7E]/g,'')['trim']();}function parseZeusSse(_0x1d9f07,_0xad71cc){var _0x400da1={_0x3eb75f:0x7a,_0x5bd498:0xb4,_0x140d14:0x90,_0x1eaf86:0xbb,_0x21fadb:0xb7,_0x43acec:0xa0,_0x118f3a:0x8d,_0x491875:0xb0,_0x33c443:0xa0,_0x10355f:0xa0,_0x2559e7:0x8f,_0x407a39:0x7d,_0x59ca4d:0xa8,_0x3e806a:0xb1},_0x83b8e0=_0x1d62d1,_0x5c6252=[],_0x2cb7a8=_0x1d9f07[_0x83b8e0(_0x400da1._0x3eb75f)]('\x0a'),_0x4cdf12=null;for(var _0x6060de=0x0;_0x6060de<_0x2cb7a8['length'];_0x6060de++){var _0x1f7211=_0x2cb7a8[_0x6060de]['trim']();if(_0x1f7211['indexOf'](_0x83b8e0(_0x400da1._0x5bd498))===0x0){_0x4cdf12=_0x1f7211[_0x83b8e0(0x84)]('event:','')[_0x83b8e0(0x79)]();continue;}if(_0x1f7211[_0x83b8e0(_0x400da1._0x140d14)]('data:')===0x0&&_0x4cdf12==='sources')try{var _0x1b69c1=JSON['parse'](_0x1f7211['replace'](_0x83b8e0(0xb9),'')['trim']()),_0x4cdfe3=_0x1b69c1[_0x83b8e0(0xa2)]||[];for(var _0x2d5197=0x0;_0x2d5197<_0x4cdfe3['length'];_0x2d5197++){var _0x331e9f=_0x4cdfe3[_0x2d5197];if(!_0x331e9f['url']||_0x331e9f[_0x83b8e0(_0x400da1._0x1eaf86)])continue;var _0x14c353=null,_0x336418=ZEUS_REFERER,_0x5d1458=_0x331e9f['format']||_0x83b8e0(_0x400da1._0x21fadb),_0x2f0fc3=_0x331e9f[_0x83b8e0(0xa0)]['match'](/[?&]stream=([^&]+)/);if(_0x2f0fc3)_0x14c353=ZEUS_BASE+(_0x331e9f[_0x83b8e0(0xa0)][_0x83b8e0(0x7f)](0x0)==='?'?_0x331e9f[_0x83b8e0(_0x400da1._0x43acec)]:'?'+_0x331e9f['url']),_0x5d1458='mp4';else{var _0xac2136=_0x331e9f[_0x83b8e0(0xa0)][_0x83b8e0(0xa5)](/[?&]proxy=([^&]+)/);if(_0xac2136){var _0x2e102d=b64decode(_0xac2136[0x1]);if(_0x2e102d&&_0x2e102d[_0x83b8e0(0x90)](_0x83b8e0(_0x400da1._0x118f3a))===0x0){if(_0x2e102d[_0x83b8e0(0x90)](_0x83b8e0(_0x400da1._0x491875))!==-0x1)continue;_0x14c353=_0x2e102d,_0x5d1458=_0x83b8e0(0x94);var _0x144684=_0x331e9f[_0x83b8e0(0xa0)]['match'](/[?&]ref=([^&]+)/);if(_0x144684){var _0x5a080d=b64decode(_0x144684[0x1]);_0x5a080d&&_0x5a080d['indexOf']('http')===0x0&&(_0x336418=_0x5a080d);}}else _0x14c353=ZEUS_BASE+(_0x331e9f[_0x83b8e0(_0x400da1._0x33c443)]['charAt'](0x0)==='?'?_0x331e9f[_0x83b8e0(_0x400da1._0x10355f)]:'?'+_0x331e9f[_0x83b8e0(0xa0)]),_0x5d1458='mp4';}}if(!_0x14c353)continue;var _0x2c6884=(_0x331e9f['lang']||'VF')[_0x83b8e0(_0x400da1._0x2559e7)](),_0x2057be=_0x331e9f['quality']||'HD',_0x371bb1=(_0x331e9f[_0x83b8e0(0x8c)]||_0x83b8e0(_0x400da1._0x407a39))[_0x83b8e0(0x8f)]();_0x5c6252[_0x83b8e0(_0x400da1._0x59ca4d)]({'name':_0x83b8e0(_0x400da1._0x3e806a)+_0x371bb1,'title':_0xad71cc(_0x331e9f,_0x2c6884,_0x2057be),'url':_0x14c353,'quality':_0x2057be,'format':_0x5d1458,'headers':{'Referer':_0x336418,'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36'}});}}catch(_0x167901){}}return _0x5c6252;}function fetchZeusUrl(_0xc8d3bd,_0x310f63){var _0x150a9d={_0x110763:0xb8,_0x219b50:0xaa},_0x14e4a3=_0x1d62d1;return fetch(_0xc8d3bd,{'headers':{'Referer':ZEUS_REFERER,'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36','Accept':'text/event-stream'}})['then'](function(_0x883326){var _0x5a1a04=_0x4e7c;if(!_0x883326['ok'])throw new Error(_0x5a1a04(0x99)+_0x883326[_0x5a1a04(0x7e)]);return _0x883326['text']();})[_0x14e4a3(0xab)](function(_0x959e85){var _0x52a4ea=_0x14e4a3,_0x3375ac=parseZeusSse(_0x959e85,_0x310f63);if(_0x3375ac[_0x52a4ea(_0x150a9d._0x110763)]===0x0)throw new Error(_0x52a4ea(_0x150a9d._0x219b50));return _0x3375ac;});}function fetchMovieFastFlux(_0x2ecf2f,_0xd491c2,_0x6026cb){var _0x4c7a43={_0x3c2af9:0xa4},_0x3c6f78={_0x25e8a1:0x96,_0x2b039c:0x76,_0x143905:0xa7,_0x5a7012:0x95},_0xeed071=_0x1d62d1;return callApi(_0x2ecf2f,_0xd491c2,{'api':_0xeed071(_0x4c7a43._0x3c2af9),'endpoint':'movie','tmdb_id':String(_0x6026cb)})['then'](function(_0x474450){var _0x559eba=_0xeed071;if(!_0x474450||!_0x474450['success']||!_0x474450['source_url'])throw new Error('Film\x20non\x20disponible');return[{'name':_0x559eba(_0x3c6f78._0x25e8a1),'title':(_0x474450[_0x559eba(_0x3c6f78._0x2b039c)]||'ToFlix')+_0x559eba(_0x3c6f78._0x143905),'url':_0x474450['source_url'],'quality':'HD','format':_0x474450['source']&&_0x474450[_0x559eba(0x78)]['type']==='m3u8'?'m3u8':'mp4','headers':{'Referer':_0xd491c2,'User-Agent':_0x559eba(_0x3c6f78._0x5a7012)}}];});}function fetchMovieZeus(_0xcd7b64){var _0xfba48b=_0x1d62d1,_0x5afb4f=ZEUS_BASE+_0xfba48b(0x9b)+_0xcd7b64;return fetchZeusUrl(_0x5afb4f,function(_0x21a42e,_0x437da9,_0x12ce3e){var _0x2fe84a=_0xfba48b;return(_0x21a42e['name']||'ToFlix')+_0x2fe84a(0x9e)+_0x437da9+'\x20'+_0x12ce3e;});}function fetchMovie(_0x3ec1e1,_0x4deb88,_0x55f25a){var _0x5c117e={_0x535d8e:0xaf},_0x256732={_0x5c3756:0xb8},_0x30813f=_0x1d62d1,_0x35d6cd=fetchMovieFastFlux(_0x3ec1e1,_0x4deb88,_0x55f25a)['catch'](function(){return[];}),_0x3277c8=fetchMovieZeus(_0x55f25a)[_0x30813f(0x7c)](function(){return[];});return Promise[_0x30813f(_0x5c117e._0x535d8e)]([_0x35d6cd,_0x3277c8])['then'](function(_0x575b09){var _0x338c5e=_0x30813f,_0x1e51c9=_0x575b09[0x0][_0x338c5e(0x92)](_0x575b09[0x1]);if(_0x1e51c9[_0x338c5e(_0x256732._0x5c3756)]===0x0)throw new Error(_0x338c5e(0x97));return _0x1e51c9;});}function fetchSeriesFastFlux(_0x5057f7,_0x506029,_0x4ef3f1,_0x49e409,_0x3fed2d){var _0x52df89={_0x4efc82:0xa6},_0x5a15ba={_0x3379ee:0xa0,_0x382bb6:0xa0,_0x1a0ff4:0x9e,_0x14e614:0x76},_0x200593=_0x1d62d1;return callApi(_0x5057f7,_0x506029,{'api':_0x200593(0xa4),'endpoint':_0x200593(_0x52df89._0x4efc82),'tmdb_id':String(_0x4ef3f1)})['then'](function(_0x19998b){var _0x597d95=_0x200593;if(!_0x19998b||!_0x19998b['success']||!_0x19998b[_0x597d95(0x77)])throw new Error('FastFlux\x20non\x20disponible');var _0x37b3d0=String(_0x49e409);if(!_0x19998b[_0x597d95(0x77)][_0x37b3d0])throw new Error('Saison\x20'+_0x49e409+_0x597d95(0x9c));var _0x162174=_0x19998b['seasons'][_0x37b3d0];for(var _0x1eb8ad=0x0;_0x1eb8ad<_0x162174[_0x597d95(0xb8)];_0x1eb8ad++){var _0x196003=_0x162174[_0x1eb8ad];if(_0x196003['episode_number']===_0x3fed2d){var _0x31e2e9=_0x196003[_0x597d95(_0x5a15ba._0x3379ee)]||_0x196003['source']&&_0x196003['source'][_0x597d95(_0x5a15ba._0x382bb6)];if(!_0x31e2e9)throw new Error('URL\x20non\x20trouvee\x20pour\x20S'+_0x49e409+'E'+_0x3fed2d);return[{'name':_0x597d95(0x96),'title':'S'+_0x49e409+'E'+_0x3fed2d+_0x597d95(_0x5a15ba._0x1a0ff4)+(_0x196003[_0x597d95(_0x5a15ba._0x14e614)]||'VF'),'url':_0x31e2e9,'quality':'HD','format':_0x31e2e9['indexOf']('.m3u8')!==-0x1?'m3u8':'mp4','headers':{'Referer':_0x506029,'User-Agent':_0x597d95(0x95)}}];}}throw new Error(_0x597d95(0xbd)+_0x49e409+'E'+_0x3fed2d+_0x597d95(0xad));});}function fetchSeriesZeus(_0x2b04f7,_0x5ef391,_0x1425d3){var _0x7cddfe={_0x59d799:0x87},_0x481a97=_0x1d62d1,_0x21dd8b=ZEUS_BASE+_0x481a97(_0x7cddfe._0x59d799)+_0x2b04f7+_0x481a97(0xbe)+_0x5ef391+'&e='+_0x1425d3;return fetchZeusUrl(_0x21dd8b,function(_0x3705ee,_0x3dbd03,_0x51577b){var _0x5465f1=_0x481a97;return'S'+_0x5ef391+'E'+_0x1425d3+'\x20-\x20'+(_0x3705ee[_0x5465f1(0x86)]||_0x3dbd03)+'\x20'+_0x51577b;});}function fetchSeries(_0xfabeb8,_0x432a7f,_0x1da6d1,_0x5cca1d,_0xb713ce){var _0x2c2012={_0x497d66:0x7c},_0x2837d2={_0x4d47a3:0xb8},_0x3e4be2=_0x1d62d1,_0x641446=_0x5cca1d||0x1,_0x4f1ca2=_0xb713ce||0x1,_0x2e70ae=fetchSeriesFastFlux(_0xfabeb8,_0x432a7f,_0x1da6d1,_0x641446,_0x4f1ca2)['catch'](function(){return[];}),_0x567c4f=fetchSeriesZeus(_0x1da6d1,_0x641446,_0x4f1ca2)[_0x3e4be2(_0x2c2012._0x497d66)](function(){return[];});return Promise['all']([_0x2e70ae,_0x567c4f])['then'](function(_0x5d89b3){var _0x235651=_0x3e4be2,_0x41d410=_0x5d89b3[0x0]['concat'](_0x5d89b3[0x1]);if(_0x41d410[_0x235651(_0x2837d2._0x4d47a3)]===0x0)throw new Error(_0x235651(0xb3));return _0x41d410;});}function getStreamsWithApi(_0x46fbf3,_0x72b4b4,_0x5c699d,_0x5b9507,_0x5ddae6,_0x53fcb5){if(_0x5b9507==='tv')return fetchSeries(_0x46fbf3,_0x72b4b4,_0x5c699d,_0x5ddae6,_0x53fcb5);return fetchMovie(_0x46fbf3,_0x72b4b4,_0x5c699d);}function getStreams(_0x2ec765,_0x336eac,_0x221875,_0x18db2c,_0x42646f){var _0x106ecf={_0x5831f7:0x7c},_0x1eaafd={_0x4cd952:0x91},_0x5953c8=_0x1d62d1;return detectToflixEndpoint()['then'](function(_0xd5db3c){var _0x18ada4=_0x4e7c;return TOFLIX_API=_0xd5db3c[_0x18ada4(_0x1eaafd._0x4cd952)],TOFLIX_REFERER=_0xd5db3c['referer'],ZEUS_REFERER=_0xd5db3c[_0x18ada4(0x9d)],getStreamsWithApi(_0xd5db3c[_0x18ada4(0x91)],_0xd5db3c['referer'],_0x2ec765,_0x336eac,_0x221875,_0x18db2c);})[_0x5953c8(_0x106ecf._0x5831f7)](function(_0x21177c){var _0x328a4c=_0x5953c8;return console['error']('[ToFlix]\x20Erreur:',_0x21177c[_0x328a4c(0x85)]||_0x21177c),[];});}typeof module!=='undefined'&&module['exports']?module['exports']={'getStreams':getStreams}:global['getStreams']=getStreams;

/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:ccebe621bb93 */
;(function(g,config){
  "use strict";
  function clean(v){return String(v==null?"":v).replace(/^\uFEFF/,"").replace(/^ï»¿/,"").trim()}
  function hlsHint(stream){
    if(!stream||typeof stream!=="object")return false;
    var u=String(stream.url||"").toLowerCase(),t=String(stream.type||stream.format||"").toLowerCase();
    return /\.m3u8(?:[?#]|$)/i.test(u)||u.indexOf("/hls/")>=0||u.indexOf("/hls2/")>=0||t==="hls"||t==="m3u8"||t.indexOf("mpegurl")>=0;
  }
  function absolute(raw,base){try{return new URL(clean(raw),base).toString()}catch(_e){return ""}}
  function requestHeaders(stream){
    var src=stream&&stream.headers&&typeof stream.headers==="object"?stream.headers:{};
    var out={};Object.keys(src).forEach(function(k){out[k]=String(src[k])});
    if(!out.Accept)out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,text/plain,*/*";
    return out;
  }
  async function fetchText(url,stream){
    if(!g||typeof g.fetch!=="function")return {state:"unknown",reason:"fetch_unavailable"};
    var controller=typeof AbortController!=="undefined"?new AbortController():null;
    var timer=setTimeout(function(){try{if(controller)controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var body=clean(await response.text());
      return {state:"ok",body:body,url:String(response.url||url),contentType:String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"")};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{clearTimeout(timer);try{if(controller)controller.abort()}catch(_e){}}
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
  async function validateChild(url,stream){
    var result=await fetchText(url,stream);if(result.state!=="ok")return result.state;
    var kind=playlistKind(result.body);return kind==="media"||kind==="master"?"valid":"invalid";
  }
  async function validateHls(stream){
    var result=await fetchText(String(stream.url||""),stream);
    if(result.state!=="ok")return result.state;
    var kind=playlistKind(result.body);
    if(kind==="invalid"||kind==="header_only")return "invalid";
    if(kind==="media")return "valid";

    var variants=variantUris(result.body,result.url||stream.url),audio=audioUris(result.body,result.url||stream.url);
    if(!variants.length)return "invalid";
    var variantState="invalid";
    for(var i=0;i<variants.length;i++){
      var s=await validateChild(variants[i],stream);if(s==="valid"){variantState="valid";break}if(s==="unknown")variantState="unknown";
    }
    if(variantState!=="valid")return variantState;
    if(audio.length){
      var audioState="invalid";
      for(var j=0;j<audio.length;j++){
        var a=await validateChild(audio[j],stream);if(a==="valid"){audioState="valid";break}if(a==="unknown")audioState="unknown";
      }
      if(audioState!=="valid")return audioState;
    }
    return "valid";
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!hlsHint(stream))return stream;
      var state=await validateHls(stream);
      if(state==="invalid"){
        try{console.warn("[Nuvio HLS integrity] rejected malformed playlist",String(stream&&stream.url||"").slice(0,180))}catch(_e){}
        return null;
      }
      return stream;
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
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2});
