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
})(typeof globalThis!=="undefined"?globalThis:this,"eyJncm91cHMiOlt7ImNhbmRpZGF0ZXMiOlsiaHR0cHM6Ly9laW50aHVzYW4uYXNhZGRvbi5jb20iLCJodHRwczovL2VpbnRodXNhbi50diIsImh0dHBzOi8vY2RuMi5laW50aHVzYW4uaW8iXSwiaG9zdHMiOlsiZWludGh1c2FuLmFzYWRkb24uY29tIiwiZWludGh1c2FuLnR2IiwiY2RuMi5laW50aHVzYW4uaW8iXX1dLCJyZXZpc2lvbiI6InJldHJ5LXRyYW5zaWVudC12MiJ9");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */
'use strict';const _0x1441be=_0x2a19;(function(_0x8910e3,_0x522a64){const _0x3c8156={_0x14f49:0x1a0,_0x3a8d3e:0x1b5,_0x4d6854:0x1bb,_0x494d92:0x1a8,_0x542e65:0x1bd},_0x2088a6=_0x2a19,_0x3d69ea=_0x8910e3();while(!![]){try{const _0x5463a7=parseInt(_0x2088a6(_0x3c8156._0x14f49))/0x1+-parseInt(_0x2088a6(0x1a2))/0x2*(parseInt(_0x2088a6(0x199))/0x3)+parseInt(_0x2088a6(0x1a9))/0x4+-parseInt(_0x2088a6(_0x3c8156._0x3a8d3e))/0x5*(parseInt(_0x2088a6(_0x3c8156._0x4d6854))/0x6)+parseInt(_0x2088a6(0x172))/0x7*(parseInt(_0x2088a6(_0x3c8156._0x494d92))/0x8)+-parseInt(_0x2088a6(_0x3c8156._0x542e65))/0x9*(-parseInt(_0x2088a6(0x197))/0xa)+-parseInt(_0x2088a6(0x17d))/0xb*(-parseInt(_0x2088a6(0x1bf))/0xc);if(_0x5463a7===_0x522a64)break;else _0x3d69ea['push'](_0x3d69ea['shift']());}catch(_0x1e9f95){_0x3d69ea['push'](_0x3d69ea['shift']());}}}(_0x4b0c,0x54215));var __defProp=Object['defineProperty'],__defProps=Object[_0x1441be(0x1ae)],__getOwnPropDescs=Object['getOwnPropertyDescriptors'],__getOwnPropSymbols=Object['getOwnPropertySymbols'],__hasOwnProp=Object['prototype'][_0x1441be(0x1ab)],__propIsEnum=Object[_0x1441be(0x184)][_0x1441be(0x1be)],__defNormalProp=(_0x4e0f51,_0x4c3e66,_0x6ec5e9)=>_0x4c3e66 in _0x4e0f51?__defProp(_0x4e0f51,_0x4c3e66,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x6ec5e9}):_0x4e0f51[_0x4c3e66]=_0x6ec5e9,__spreadValues=(_0x5ed0d0,_0x425273)=>{const _0x498949=_0x1441be;for(var _0x4279c2 in _0x425273||(_0x425273={}))if(__hasOwnProp['call'](_0x425273,_0x4279c2))__defNormalProp(_0x5ed0d0,_0x4279c2,_0x425273[_0x4279c2]);if(__getOwnPropSymbols)for(var _0x4279c2 of __getOwnPropSymbols(_0x425273)){if(__propIsEnum[_0x498949(0x189)](_0x425273,_0x4279c2))__defNormalProp(_0x5ed0d0,_0x4279c2,_0x425273[_0x4279c2]);}return _0x5ed0d0;},__spreadProps=(_0x3a6abd,_0x5c1c84)=>__defProps(_0x3a6abd,__getOwnPropDescs(_0x5c1c84)),__async=(_0x529aee,_0x59d272,_0x111b3b)=>{return new Promise((_0x16e579,_0x567020)=>{const _0x4b7303={_0x24616c:0x1b9},_0x55bb92=_0x2a19;var _0x235343=_0x53fdbe=>{const _0x314a85=_0x2a19;try{_0x3c52b1(_0x111b3b[_0x314a85(_0x4b7303._0x24616c)](_0x53fdbe));}catch(_0x58b498){_0x567020(_0x58b498);}},_0x3fc91e=_0x1b8684=>{try{_0x3c52b1(_0x111b3b['throw'](_0x1b8684));}catch(_0x227f7e){_0x567020(_0x227f7e);}},_0x3c52b1=_0x44bf2b=>_0x44bf2b[_0x55bb92(0x192)]?_0x16e579(_0x44bf2b[_0x55bb92(0x1c1)]):Promise['resolve'](_0x44bf2b['value'])[_0x55bb92(0x1b6)](_0x235343,_0x3fc91e);_0x3c52b1((_0x111b3b=_0x111b3b['apply'](_0x529aee,_0x59d272))[_0x55bb92(0x1b9)]());});};function onSettings(){const _0x15efe0={_0x3bd153:0x1ac,_0x3de0aa:0x1a5,_0xab4b82:0x1ac,_0x2b3579:0x1bc,_0x1c1f42:0x183,_0x38099d:0x178};return __async(this,null,function*(){const _0x3d0bfc=_0x2a19;return[{'type':'header','label':'Language\x20Preferences'},{'type':_0x3d0bfc(_0x15efe0._0x3bd153),'key':_0x3d0bfc(0x1a6),'label':'Enable\x20Hindi\x20🇮🇳','defaultValue':!![]},{'type':'toggle','key':_0x3d0bfc(_0x15efe0._0x3de0aa),'label':_0x3d0bfc(0x19f),'defaultValue':!![]},{'type':_0x3d0bfc(_0x15efe0._0xab4b82),'key':_0x3d0bfc(_0x15efe0._0x2b3579),'label':'Enable\x20Telugu\x20🇮🇳','defaultValue':!![]},{'type':_0x3d0bfc(_0x15efe0._0x3bd153),'key':_0x3d0bfc(_0x15efe0._0x1c1f42),'label':'Enable\x20Malayalam\x20🇮🇳','defaultValue':!![]},{'type':'toggle','key':'langKannada','label':'Enable\x20Kannada\x20🇮🇳','defaultValue':!![]},{'type':'toggle','key':_0x3d0bfc(_0x15efe0._0x38099d),'label':'Enable\x20Bengali\x20🇧🇩','defaultValue':!![]}];});}var EINTHUSAN_BASE='https://einthusan.asaddon.com',TMDB_API_KEY=_0x1441be(0x188),PROVIDER_NAME='Einthusan',LANGUAGES={'langHindi':{'path':_0x1441be(0x1a7),'label':'Hindi\x20🇮🇳','webCode':_0x1441be(0x1a7)},'langTamil':{'path':_0x1441be(0x1b3),'label':_0x1441be(0x1c5),'webCode':_0x1441be(0x1b3)},'langTelugu':{'path':_0x1441be(0x1b1),'label':'Telugu','webCode':'telugu'},'langMalayalam':{'path':'malayalam','label':'Malayalam','webCode':_0x1441be(0x198)},'langKannada':{'path':_0x1441be(0x182),'label':'Kannada','webCode':'kannada'},'langBengali':{'path':'bengali','label':'Bengali\x20🇧🇩','webCode':_0x1441be(0x19a)}},LANGUAGE_ORDER=['hindi',_0x1441be(0x1b3),'telugu',_0x1441be(0x198),'kannada',_0x1441be(0x19a)],DEFAULT_HEADERS={'User-Agent':_0x1441be(0x191),'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','Accept-Language':_0x1441be(0x1c3)},sessionCache={};function getSession(_0x5c84e8){const _0x19b855=_0x1441be,_0x8e7a7=sessionCache['session_'+_0x5c84e8];if(!_0x8e7a7)return null;if(Date['now']()-_0x8e7a7['createdAt']>2.5*0x3c*0x3c*0x3e8)return delete sessionCache[_0x19b855(0x1a4)+_0x5c84e8],null;return _0x8e7a7['cookieString'];}function parseAndCombineCookies(_0x1859fb,_0x8095e4){const _0x460241={_0x429f21:0x16d},_0x4d1aa1={_0x7b6ea8:0x16c,_0x3bfde8:0x175},_0x288924=_0x1441be;if(!_0x8095e4)return _0x1859fb;const _0x50b3dd={};_0x1859fb&&_0x1859fb[_0x288924(_0x460241._0x429f21)](';')['forEach'](_0x35f575=>{const _0x1de3bd=_0x288924,_0x16e8d4=_0x35f575[_0x1de3bd(0x16d)]('=');if(_0x16e8d4[0x0])_0x50b3dd[_0x16e8d4[0x0]['trim']()]=_0x16e8d4['slice'](0x1)[_0x1de3bd(0x16c)]('=')[_0x1de3bd(0x175)]();});const _0x5d1806=Array['isArray'](_0x8095e4)?_0x8095e4:[_0x8095e4];return _0x5d1806['forEach'](_0x523644=>{const _0x57276a=_0x288924;_0x523644['split'](',')[_0x57276a(0x196)](_0x3b1c0a=>{const _0x386e77=_0x57276a,_0x53286b=_0x3b1c0a['split'](';')[0x0]['split']('=');_0x53286b[0x0]&&_0x53286b[0x1]&&(_0x50b3dd[_0x53286b[0x0]['trim']()]=_0x53286b['slice'](0x1)[_0x386e77(_0x4d1aa1._0x7b6ea8)]('=')[_0x386e77(_0x4d1aa1._0x3bfde8)]());});}),Object['entries'](_0x50b3dd)['map'](([_0x23516c,_0xec12e7])=>_0x23516c+'='+_0xec12e7)['join'](';\x20');}function loginAndGetCookies(_0x5c0d96,_0x13e493,_0x80eb92){const _0x4b31be={_0x48b506:0x187,_0x48028e:0x16b,_0x3aa430:0x177};return __async(this,null,function*(){const _0x20ac04=_0x2a19;if(!_0x5c0d96||!_0x13e493)return'';const _0x2a6cba=getSession(_0x5c0d96);if(_0x2a6cba)return _0x2a6cba;try{const _0x1db3c0='https://einthusan.tv/account/login/?lang='+_0x80eb92,_0x8ce600=yield fetch(_0x1db3c0,{'headers':DEFAULT_HEADERS}),_0x3e34c5=yield _0x8ce600[_0x20ac04(0x1a1)](),_0x2e10a2=_0x3e34c5['match'](/name="(?:csrfmiddlewaretoken|_token)"\s+value="([^"]+)"/)||_0x3e34c5['match'](/value="([^"]+)"\s+name="(?:csrfmiddlewaretoken|_token)"/),_0x5d36f9=_0x2e10a2?_0x2e10a2[0x1]:'',_0x1f4dd9=_0x8ce600['headers']['getSetCookie']?_0x8ce600['headers'][_0x20ac04(0x16b)]():_0x8ce600[_0x20ac04(_0x4b31be._0x48b506)]['get'](_0x20ac04(0x18c));let _0x2772f8=parseAndCombineCookies('',_0x1f4dd9);const _0x278b04=new URLSearchParams({'csrfmiddlewaretoken':_0x5d36f9,'email':_0x5c0d96,'password':_0x13e493,'next':'/'}),_0x14be65=yield fetch(_0x1db3c0,{'method':'POST','headers':__spreadProps(__spreadValues({},DEFAULT_HEADERS),{'Content-Type':_0x20ac04(0x1c6),'Cookie':_0x2772f8,'Referer':_0x1db3c0}),'body':_0x278b04[_0x20ac04(0x181)](),'redirect':_0x20ac04(0x185)}),_0x23e858=_0x14be65['headers'][_0x20ac04(0x16b)]?_0x14be65['headers'][_0x20ac04(_0x4b31be._0x48028e)]():_0x14be65[_0x20ac04(0x187)]['get'](_0x20ac04(0x18c));_0x2772f8=parseAndCombineCookies(_0x2772f8,_0x23e858);if(!_0x2772f8['includes']('sid='))return'';return sessionCache['session_'+_0x5c0d96]={'cookieString':_0x2772f8,'createdAt':Date[_0x20ac04(_0x4b31be._0x3aa430)]()},_0x2772f8;}catch(_0x53639f){return'';}});}function scrapePremiumTokens(_0x365b2d,_0x30203e,_0x1bf7b9,_0x477561){const _0x3acd63={_0x544663:0x170,_0x12c010:0x1ad};return __async(this,null,function*(){const _0x5de562=_0x2a19;try{const _0x5d1a3e=_0x1bf7b9?'serial':_0x5de562(0x19b),_0x10d115='https://einthusan.tv/'+(_0x477561?'premium/':'')+_0x5d1a3e+_0x5de562(0x186)+_0x365b2d+_0x5de562(0x176)+(_0x30203e||'hindi')+'&uhd=true',_0x3842b6=__spreadProps(__spreadValues({},DEFAULT_HEADERS),{'Referer':'https://einthusan.tv/'});if(_0x477561)_0x3842b6[_0x5de562(_0x3acd63._0x544663)]=_0x477561;const _0x852dd6=yield fetch(_0x10d115,{'headers':_0x3842b6});if(!_0x852dd6['ok'])return null;const _0x5a8ff8=yield _0x852dd6['text'](),_0x3835ce=/data-m3u8=["']([^"']*\.mp4(?:\.m3u8)?\?[^"']+)["']/,_0xb05629=_0x5a8ff8[_0x5de562(0x16f)](_0x3835ce);if(_0xb05629&&_0xb05629[0x1]){const _0x135ef2=_0xb05629[0x1]['replace'](/&amp;/g,'&'),_0x93e2ca=_0x135ef2['match'](/[?&](e=\d+&md5=[a-zA-Z0-9_=-]+)/);if(_0x93e2ca)return _0x93e2ca[0x1];}const _0x1a6827=/content\/[DB][^.]+\.mp4(?:\.m3u8)?\?(e=\d+&amp;md5=[a-zA-Z0-9_=-]+)/,_0x3738e4=_0x5a8ff8['match'](_0x1a6827);if(_0x3738e4)return _0x3738e4[0x1][_0x5de562(_0x3acd63._0x12c010)](/&amp;/g,'&');}catch(_0x3940b4){console['error']('Token\x20structural\x20parsing\x20error:',_0x3940b4);}return null;});}function getTmdbMeta(_0x3f9bc5,_0x3fa2a6){const _0x112627={_0x2cc1a9:0x19c};return __async(this,null,function*(){const _0x37f69a=_0x2a19,_0x35edbf=_0x3fa2a6==='tv'?'tv':'movie',_0x5cf660=_0x37f69a(_0x112627._0x2cc1a9)+_0x35edbf+'/'+_0x3f9bc5+'?api_key='+TMDB_API_KEY+'&append_to_response=external_ids';try{const _0x31d786=yield fetch(_0x5cf660);if(!_0x31d786['ok'])return null;return yield _0x31d786['json']();}catch(_0x227cb9){return null;}});}var pad2=_0x2e2387=>String(Number[_0x1441be(0x194)](_0x2e2387!=null?_0x2e2387:0x0,0xa)||0x0)['padStart'](0x2,'0'),isProxyUrl=_0x114578=>String(_0x114578!=null?_0x114578:'')[_0x1441be(0x169)]('workers.dev')||/[?&]url=/['test'](String(_0x114578!=null?_0x114578:''));function resolveProxyUrl(_0x521704){const _0x24e4b2={_0x14353a:0x1c2,_0x501467:0x17b,_0x521083:0x187,_0x4aff69:0x17f,_0xd19531:0x1a1};return __async(this,null,function*(){const _0x152560=_0x2a19;var _0x56613c,_0x107e58,_0x502c31,_0x3e8929;try{const _0x3bcae9=yield fetch(_0x521704,{'redirect':_0x152560(_0x24e4b2._0x14353a),'headers':__spreadProps(__spreadValues({},DEFAULT_HEADERS),{'Referer':_0x521704})}),_0x456023=_0x3bcae9[_0x152560(0x171)];if(['.m3u8',_0x152560(0x179),_0x152560(0x1ba)][_0x152560(_0x24e4b2._0x501467)](_0x59bed4=>_0x456023['includes'](_0x59bed4)))return _0x456023;const _0x1b89b8=(_0x56613c=_0x3bcae9[_0x152560(_0x24e4b2._0x521083)][_0x152560(_0x24e4b2._0x4aff69)](_0x152560(0x1af)))!=null?_0x56613c:'';if(_0x1b89b8['includes']('text/plain'))return(yield _0x3bcae9[_0x152560(_0x24e4b2._0xd19531)]())['trim']();if(_0x1b89b8['includes']('application/json')){const _0x2ddbbc=yield _0x3bcae9['json']();return(_0x3e8929=(_0x502c31=(_0x107e58=_0x2ddbbc==null?void 0x0:_0x2ddbbc['url'])!=null?_0x107e58:_0x2ddbbc==null?void 0x0:_0x2ddbbc['stream'])!=null?_0x502c31:_0x2ddbbc==null?void 0x0:_0x2ddbbc[_0x152560(0x1aa)])!=null?_0x3e8929:null;}return _0x456023;}catch(_0x44ef1e){return null;}});}function fetchStreams(_0x1c1ecb){const _0x4b213e={_0x3459be:0x18a,_0x1f4ce0:0x18a};return __async(this,null,function*(){const _0x31f5d9=_0x2a19;try{const _0xc415=yield fetch(_0x1c1ecb);if(!_0xc415['ok'])return[];const _0x27f17a=yield _0xc415['json']();if(!Array['isArray'](_0x27f17a==null?void 0x0:_0x27f17a[_0x31f5d9(_0x4b213e._0x3459be)]))return[];return _0x27f17a[_0x31f5d9(_0x4b213e._0x1f4ce0)]['filter'](_0xdc5402=>typeof(_0xdc5402==null?void 0x0:_0xdc5402[_0x31f5d9(0x171)])===_0x31f5d9(0x17e)&&_0xdc5402['url']['startsWith'](_0x31f5d9(0x17a)));}catch(_0x5ab11b){return[];}});}function _0x4b0c(){const _0x88d625=['z2v0u2v0q29VA2LL','AM9PBG','C3bSAxq','ywXS','Bwf0y2G','q29VA2LL','DxjS','mteZmJy3wfvJuune','ic0Gka','8j+oPIa','DhjPBq','lZ9Syw5Npq','BM93','BgfUz0jLBMDHBgK','lM1Wna','Ahr0Chm','C29Tzq','cVcFJP7VUi8Gtva0ihWG8j+uLYaOq0romIdIGkiGuhjLBwL1BsK','ntuXmJu0BhPrEfPl','C3rYAw5N','z2v0','BgfIzwW','Dg9tDhjPBMC','A2fUBMfKyq','BgfUz01HBgf5ywXHBq','ChjVDg90ExbL','BwfUDwfS','l3DHDgnOlW','AgvHzgvYCW','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','y2fSBa','C3rYzwfTCW','z2v0u3rYzwfTCW','C2v0lwnVB2TPzq','BgfUz0TLEq','Aw1KyL9Pza','D2vIq29Kzq','cUkAOsaXmdGWCcb8ipcFL6pVUi8G','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmc4WlJaUmcbtywzHCMKVntm3lJm2','zg9Uzq','zxjYB3i','CgfYC2vjBNq','C2vYAwvZ','zM9YrwfJAa','mtbSzKLvq2i','BwfSyxLHBgfT','m3HuwvbmwG','yMvUz2fSAq','Bw92Awu','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','Cgf0Aa','BMfTzq','rw5HyMXLifrHBwLSipcFH67WN4EZ','nduWnta5BNPTCNjA','Dgv4Da','nZq1odG2BLv5ruXh','zxH0zxjUywXvCMW','C2vZC2LVBL8','BgfUz1rHBwLS','BgfUz0HPBMrP','AgLUzgK','ndHJsgfvEee','mJuYntG4twrtAuj2','C3jJ','AgfZt3DUuhjVCgvYDhK','Dg9Nz2XL','CMvWBgfJzq','zgvMAw5LuhjVCgvYDgLLCW','y29UDgvUDc10ExbL','yMvOyxzPB3jiAw50CW','DgvSDwD1','Aw5KzxHpzG','DgfTAwW','Ahr0Chm6lY9Jzg4XlMvPBNrODxnHBI5PBY9LDhyVy29UDgvUDc9e','nJa1BePSz1vs','DgHLBG','zMLYC3rFywLYx2rHDgu','zw50CMLLCW','BMv4Da','lM1RDG','mtC4mtrqsvrjCKm','BgfUz1rLBhvNDq','ntG2mJe1vg5ds3fc','ChjVCgvYDhLjC0vUDw1LCMfIBgu','otzJA05rsfe','z2L0AhvIlMnVBq','DMfSDwu','zM9SBg93','zw4TvvmSzw47Ct0WlJK','lM1Wnd8','vgfTAwW','yxbWBgLJyxrPB24VEc13D3CTzM9YBs11CMXLBMnVzgvK','Aw5JBhvKzxm','lMPZB24'];_0x4b0c=function(){return _0x88d625;};return _0x4b0c();}function getStreams(_0x515d4d,_0x57d093,_0x4b8a40,_0x44a3e5){const _0x1d6afd={_0x10f172:0x19e,_0x2d0b4f:0x173,_0x47b4f9:0x18e,_0x342ae0:0x16e,_0x4d993d:0x193},_0xbf5520={_0x39a3eb:0x1b2},_0x4bf437={_0x3c2bd0:0x1a3,_0xeb847f:0x171,_0x20df71:0x16f,_0x468948:0x18f,_0x50817d:0x1b4,_0x48d765:0x190};return __async(this,null,function*(){const _0x5d1122=_0x2a19;var _0x53089d;const _0x532079=_0x57d093==='tv'||_0x57d093===_0x5d1122(0x195)||_0x4b8a40!=null||_0x44a3e5!=null,_0x440911=_0x4b8a40!=null?_0x4b8a40:0x1,_0x404c16=_0x44a3e5!=null?_0x44a3e5:0x1;try{const _0x2b8081=globalThis['SCRAPER_SETTINGS']||{},_0x20879=Object[_0x5d1122(0x1b8)](LANGUAGES)['filter'](([_0xf8ac5c])=>_0x2b8081[_0xf8ac5c]!==![]),_0x42b914=yield getTmdbMeta(_0x515d4d,_0x532079?'tv':'movie'),_0x3d595f=_0x42b914?_0x42b914['title']||_0x42b914[_0x5d1122(_0x1d6afd._0x10f172)]:'Movie',_0x50245b=_0x42b914?_0x42b914['release_date']||_0x42b914[_0x5d1122(0x1b7)]||'':'',_0x2d1418=_0x50245b?_0x5d1122(_0x1d6afd._0x2d0b4f)+_0x50245b['substring'](0x0,0x4)+')':'',_0x193e24=((_0x53089d=_0x42b914==null?void 0x0:_0x42b914['external_ids'])==null?void 0x0:_0x53089d[_0x5d1122(_0x1d6afd._0x47b4f9)])||(_0x42b914==null?void 0x0:_0x42b914[_0x5d1122(_0x1d6afd._0x47b4f9)]);if(!_0x193e24)return[];const _0x3e1b6d=_0x2b8081['premiumEmail']||'',_0x589569=_0x2b8081['premiumPassword']||'',_0x23d618=[];return yield Promise[_0x5d1122(_0x1d6afd._0x342ae0)](_0x20879['map'](_0x2d6ba0=>__async(this,[_0x2d6ba0],function*([_0x475229,_0xaf8584]){const _0x517751=_0x5d1122;var _0x298b2a,_0x38c03a;const _0x15f7ac=yield loginAndGetCookies(_0x3e1b6d,_0x589569,_0xaf8584['webCode']);let _0x173de7=[];const _0xbaeca1=EINTHUSAN_BASE+'/'+_0xaf8584[_0x517751(0x19d)];!_0x532079?_0x173de7=yield fetchStreams(_0xbaeca1+'/stream/movie/'+_0x193e24+'.json'):_0x173de7=yield fetchStreams(_0xbaeca1+'/stream/series/'+_0x193e24+':'+pad2(_0x440911)+':'+pad2(_0x404c16)+_0x517751(0x16a));for(const _0x134f8b of _0x173de7){if(!(_0x134f8b==null?void 0x0:_0x134f8b['url'])||_0x134f8b[_0x517751(_0x4bf437._0x3c2bd0)]||String(_0x134f8b['url'])['includes'](_0x517751(0x1c0)))continue;let _0x38651a=isProxyUrl(_0x134f8b['url'])?yield resolveProxyUrl(_0x134f8b[_0x517751(0x171)]):_0x134f8b[_0x517751(_0x4bf437._0xeb847f)];if(!_0x38651a)continue;const _0x3d4f53=_0x38651a[_0x517751(_0x4bf437._0x20df71)](/\/content\/[DB]([^.]+)\.mp4/);if(!_0x3d4f53)continue;const _0xc1acbe=_0x3d4f53[0x1];let _0x312646='';_0x15f7ac&&(_0x312646=yield scrapePremiumTokens(_0xc1acbe,_0xaf8584[_0x517751(_0x4bf437._0x468948)],_0x532079,_0x15f7ac));if(!_0x312646){const _0x2104a5=_0x38651a[_0x517751(0x16d)]('?')[0x1];_0x312646=_0x2104a5?_0x2104a5['replace'](/&amp;/g,'&'):'';}const _0x316b82=_0x517751(_0x4bf437._0x50817d)+_0xc1acbe+'.mp4?'+_0x312646,_0x34e5ff='https://cdn2.einthusan.io/etv/content/B'+_0xc1acbe+_0x517751(0x1c4)+_0x312646,_0xabbe9a=_0xaf8584['webCode']==='hindi';if(_0xabbe9a){let _0x3e8abb=![];try{const _0x21de6b=yield fetch(_0x34e5ff,{'method':'HEAD','headers':DEFAULT_HEADERS});_0x21de6b['ok']&&(_0x3e8abb=!![]);}catch(_0x421307){_0x3e8abb=![];}if(_0x3e8abb){const _0x71f249=_0x517751(0x174)+_0x3d595f+_0x2d1418+_0x517751(_0x4bf437._0x48d765)+_0xaf8584[_0x517751(0x180)]+_0x517751(0x17c);_0x23d618['push']({'name':PROVIDER_NAME+'\x20|\x201080p\x20|\x20'+_0xaf8584[_0x517751(0x180)],'title':_0x71f249,'size':_0x71f249,'description':_0x71f249,'url':_0x34e5ff,'langKey':_0xaf8584['webCode'],'behaviorHints':(_0x298b2a=_0x134f8b['behaviorHints'])!=null?_0x298b2a:{}});}}const _0x3dbf1e='🎦\x20'+_0x3d595f+_0x2d1418+'\x0a💎\x20480p\x20|\x20🗣️\x20'+_0xaf8584['label']+'\x0a🎞️\x20MP4\x20|\x20🔗\x20(CDN1\x20•\x20Standard)';_0x23d618['push']({'name':PROVIDER_NAME+'\x20|\x20480p\x20|\x20'+_0xaf8584['label'],'title':_0x3dbf1e,'size':_0x3dbf1e,'description':_0x3dbf1e,'url':_0x316b82,'langKey':_0xaf8584['webCode'],'behaviorHints':(_0x38c03a=_0x134f8b[_0x517751(0x1b0)])!=null?_0x38c03a:{}});}}))),_0x23d618['sort']((_0x3bc2f0,_0x267176)=>{const _0x538108=_0x5d1122,_0x2a8b39=LANGUAGE_ORDER[_0x538108(0x1b2)](_0x3bc2f0[_0x538108(0x18d)]),_0x227b1e=LANGUAGE_ORDER[_0x538108(_0xbf5520._0x39a3eb)](_0x267176['langKey']),_0x5b7445=_0x2a8b39===-0x1?0x63:_0x2a8b39,_0x437802=_0x227b1e===-0x1?0x63:_0x227b1e;if(_0x5b7445!==_0x437802)return _0x5b7445-_0x437802;return _0x3bc2f0['name']['includes']('1080p')?-0x1:0x1;});}catch(_0x45dad3){return console[_0x5d1122(_0x1d6afd._0x4d993d)]('Global\x20processing\x20failure\x20context:',_0x45dad3),[];}});}function _0x2a19(_0x578b81,_0x2ea6c0){_0x578b81=_0x578b81-0x169;const _0x4b0c6c=_0x4b0c();let _0x2a19b9=_0x4b0c6c[_0x578b81];if(_0x2a19['prPEFF']===undefined){var _0x4eff08=function(_0x44f0cf){const _0xeda7c8='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x4e0f51='',_0x4c3e66='';for(let _0x6ec5e9=0x0,_0x5ed0d0,_0x425273,_0x4279c2=0x0;_0x425273=_0x44f0cf['charAt'](_0x4279c2++);~_0x425273&&(_0x5ed0d0=_0x6ec5e9%0x4?_0x5ed0d0*0x40+_0x425273:_0x425273,_0x6ec5e9++%0x4)?_0x4e0f51+=String['fromCharCode'](0xff&_0x5ed0d0>>(-0x2*_0x6ec5e9&0x6)):0x0){_0x425273=_0xeda7c8['indexOf'](_0x425273);}for(let _0x3a6abd=0x0,_0x5c1c84=_0x4e0f51['length'];_0x3a6abd<_0x5c1c84;_0x3a6abd++){_0x4c3e66+='%'+('00'+_0x4e0f51['charCodeAt'](_0x3a6abd)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x4c3e66);};_0x2a19['oMniKP']=_0x4eff08,_0x2a19['bHNkng']={},_0x2a19['prPEFF']=!![];}const _0x4ebda8=_0x4b0c6c[0x0],_0x21b3a6=_0x578b81+_0x4ebda8,_0xe854a7=_0x2a19['bHNkng'][_0x21b3a6];return!_0xe854a7?(_0x2a19b9=_0x2a19['oMniKP'](_0x2a19b9),_0x2a19['bHNkng'][_0x21b3a6]=_0x2a19b9):_0x2a19b9=_0xe854a7,_0x2a19b9;}typeof module!=='undefined'&&module['exports']?module['exports']={'getStreams':getStreams,'onSettings':onSettings}:(global[_0x1441be(0x18b)]=getStreams,global['onSettings']=onSettings);
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:26a38a47079e */
;(function(g,c){
  "use strict";
  var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
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
  function isTv(){try{var ua=String((g.navigator&&g.navigator.userAgent)||"");if(/NuvioTV|Android TV/i.test(ua))return true;if(g&&g.__NUVIO_TV_RUNTIME__===true)return true;if(typeof g.__native_fetch!=="function"||typeof g.fetch!=="function")return false;var src="";try{src=Function.prototype.toString.call(g.fetch)}catch(_e){src=String(g.fetch||"")}if(/followRedirects/.test(src))return false;var signalAware=/options\.signal|var\s+signal\s*=/.test(src);var fourArgNative=/__native_fetch\s*\(\s*url\s*,\s*method\s*,\s*JSON\.stringify\(headers\)\s*,\s*body\s*\)/.test(src);return signalAware&&fourArgNative;}catch(_e){return false}}
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=c.defaultUserAgent;
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms)}catch(_e){}
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
    }catch(e){return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"}}
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
  function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|-+)$/i.test(x)}
  function compactLanguage(row){
    var l=s(row&&row.language);if(meaningful(l))return l;
    var text=(s(row&&row.name)+" "+s(row&&row.title)).toUpperCase();
    if(/\bDUAL(?:\s+AUDIO)?\b/.test(text))return "Dual Audio";
    if(/\bVOSTFR\b/.test(text))return "VOSTFR";
    if(/\bVFQ\b/.test(text))return "VFQ";
    if(/\bVFF\b/.test(text))return "VFF";
    if(/\bVF\b/.test(text))return "VF";
    return "";
  }
  function ensurePlaybackContext(row){
    if(!row||typeof row!=="object"||mediaKind(row)==="other")return row;
    var out=Object.assign({},row),h={},has=false;
    try{var src=row.headers&&typeof row.headers==="object"?row.headers:{};Object.keys(src).forEach(function(k){if(s(src[k])){h[k]=String(src[k]);has=true}})}catch(_e){}
    if(c.defaultUserAgent&&!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=c.defaultUserAgent;has=true}
    if(has)out.headers=h;
    return out;
  }
  function tvDisplayCompat(row,tv){
    if(!tv||!row||typeof row!=="object"||meaningful(row.size))return row;
    var label=meaningful(row.description)?s(row.description):"";
    if(!label){
      var parts=[],lang=compactLanguage(row),kind=mediaKind(row);
      if(lang)parts.push(lang);
      if(kind==="hls")parts.push("HLS");else if(kind==="direct")parts.push("Direct");
      if(!parts.length&&meaningful(row.quality))parts.push(s(row.quality));
      label=parts.join(" • ");
    }
    if(!label)return row;
    var out=Object.assign({},row);out.size=label;return out;
  }
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie",url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
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
      if(c.strictPlayback||c.failClosedUnknown)return {keep:false,reason:result.reason||"unverified_media"};
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
      kept=kept.map(function(row){return tvDisplayCompat(ensurePlaybackContext(row),tv)});
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"einthusan","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:663c0a9c4d1c */
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
    var timer=null;
    if(controller&&typeof setTimeout==="function")timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",redirect:"follow",headers:requestHeaders(stream,referer,range),signal:controller?controller.signal:void 0});
      if(!response)return {state:"unknown",reason:"no_response"};
      if(response.status===404||response.status===410)return {state:"invalid",reason:"http_"+response.status};
      if(!response.ok)return {state:"unknown",reason:"http_"+response.status};
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      return {state:"ok",response:response,url:String(response.url||url),contentType:contentType};
    }catch(error){return {state:"unknown",reason:error&&error.name==="AbortError"?"timeout":"network_error"}}
    finally{if(timer!==null&&typeof clearTimeout==="function")try{clearTimeout(timer)}catch(_e){}}
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
      if(/^video\//i.test(ct))return cloneRecovered(stream,page.url,page.contentType.indexOf("webm")>=0?"webm":"mp4",item.referer);
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
    if(inspection.state==="valid")return stream;
    if(inspection.state==="unknown"&&!config.failClosedUnknown)return stream;
    if(inspection.state==="direct")return cloneRecovered(stream,inspection.url||String(stream.url||""),inspection.format||"mp4",headerValue(stream,"referer"));
    var recovered=await recover(stream,inspection);if(recovered)return recovered;
    return null;
  }
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    var checks=await Promise.all(rows.map(async function(stream){
      if(!config.probeAllUrls&&!hlsHint(stream))return stream;
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
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2,"maxRecoveryPages":4,"maxRecoveryCandidates":12,"implementationRevision":"recovery-first-v4-timer-safe"});
/* NUVIO_GLOBAL_STREAM_FACTS_V1:3f39765bf864 */
;(function(g){"use strict";
function s(v){return String(v==null?"":v).trim()}
function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|none|-+)$/i.test(x)}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function blob(row){return [row&&row.name,row&&row.title,row&&row.size,row&&row.description,row&&row.quality,row&&row.language,row&&row.codec,row&&row.audio,row&&row.sourceType,row&&row.releaseType,row&&row.format,row&&row.hdr,row&&row.videoTech,row&&row.bitDepth,row&&row.subtitles].map(s).join(" ")}
function quality(row,b){if(meaningful(row.quality)){var v=s(row.quality);return /^(?:4k|2160p)$/i.test(v)?"2160p":v}var u=b.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(row,b){if(meaningful(row.language))return s(row.language);var u=b.toUpperCase();if(/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(u))return"Multi";if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Dual Audio";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return""}
function codec(row,b){if(meaningful(row.codec))return s(row.codec);var u=b.toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return""}
function audio(row,b){if(meaningful(row.audio))return s(row.audio);var u=b.toUpperCase(),ch="",m=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(m)ch=" "+m[1];if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))return"Dolby Atmos"+ch;if(/\bTRUE[ ._-]?HD\b/.test(u))return"TrueHD"+ch;if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))return"E-AC3"+ch;if(/\bAC-?3\b/.test(u))return"AC3"+ch;if(/\bDTS[: ._-]?X\b/.test(u))return"DTS:X"+ch;if(/\bDTS[- ]?HD\b/.test(u))return"DTS-HD"+ch;if(/\bDTS\b/.test(u))return"DTS"+ch;if(/\bAAC\b/.test(u))return"AAC"+ch;return""}
function duration(row,b){if(typeof row.duration==="number"&&Number.isFinite(row.duration)&&row.duration>0)return row.duration>600?Math.round(row.duration/60):Math.round(row.duration);var direct=s(row.duration),m=direct.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=b.match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function sourceType(row,b){if(meaningful(row.sourceType))return s(row.sourceType);var u=b.toUpperCase();if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))return"BLU-RAY";if(/\bWEB[- .]?DL\b/.test(u))return"WEB-DL";if(/\bWEB[- .]?RIP\b/.test(u))return"WEBRIP";if(/\bHDTV\b/.test(u))return"HDTV";if(/\bDVD[- .]?RIP\b/.test(u))return"DVD RIP";return""}
function releaseType(row,b){if(meaningful(row.releaseType))return s(row.releaseType);return /\bREMUX\b/i.test(b)?"REMUX":""}
function formatType(row){if(meaningful(row.format))return s(row.format);var u=s(row.url).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(u))return"HLS";if(/\.mpd$/.test(u))return"DASH";if(/\.mp4$/.test(u))return"MP4";if(/\.mkv$/.test(u))return"MKV";return""}
function facts(row){if(!row||typeof row!=="object")return row;var out=Object.assign({},row),b=blob(row),q=quality(row,b),l=language(row,b),c=codec(row,b),a=audio(row,b),d=duration(row,b),st=sourceType(row,b),rt=releaseType(row,b),f=formatType(row);if(q)out.quality=q;if(l)out.language=l;if(c)out.codec=c;if(a)out.audio=a;if(d)out.duration=d;if(st)out.sourceType=st;if(rt)out.releaseType=rt;if(f)out.format=f;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamFactsV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);return x?rebuild(v,x,x.list.map(facts)):v};wrap.__nuvioGlobalStreamFactsV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this);
/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:357a581b3026 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_e){return s(v).toLowerCase()}}
function uniq(values){var out=[],seen={};(values||[]).forEach(function(v){var x=s(v),k=norm(x);if(x&&k&&!seen[k]){seen[k]=1;out.push(x)}});return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};var raw=s(q.tmdbId||q.tmdb_id||q.id||f).replace(/^tmdb:/i,"");q.tmdbId=(raw.match(/^\d+/)||[])[0]||"";q.imdbId=s(q.imdbId||q.imdb_id||"").toLowerCase();q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function episodic(q){return q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime"}
function kind(q){return episodic(q)?"tv":"movie"}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function signal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
async function jsonFetch(url){if(!g||typeof g.fetch!=="function")return null;var nb=nativeFetchBridge(),sig=nb?null:signal();if(!nb&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){var titles=uniq([q.title]),episodeTitles=[],year=q.year,imdb=q.imdbId;if(!/^\d+$/.test(q.tmdbId||""))return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb};var k=kind(q),base="https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId),d=await jsonFetch(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response=external_ids");if(d){var date=s(d.release_date||d.first_air_date);titles=uniq(titles.concat([d.title,d.name,d.original_title,d.original_name]));year=year||Number((date.match(/(?:19|20)\d{2}/)||[])[0]||0)||0;imdb=imdb||s(d.external_ids&&d.external_ids.imdb_id).toLowerCase()}if(episodic(q)&&q.season>0&&q.episode>0){var epBase=base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=";var eps=await Promise.all([jsonFetch(epBase+"fr-FR"),jsonFetch(epBase+"en-US")]);eps.forEach(function(ep){if(ep)episodeTitles=uniq(episodeTitles.concat([ep.name,ep.original_name]))})}return{titles:titles,episodeTitles:episodeTitles,year:year,imdbId:imdb}}
function episode(v){return/(?:^|\D)s(?:eason|aison)?\s*0*(\d{1,3})\s*[-_. ]*e(?:p(?:isode)?)?\s*0*(\d{1,4})(?:\D|$)/i.exec(v)||/(?:season|saison)\s*0*(\d{1,3})[^\d]{0,12}(?:episode|ep)\s*0*(\d{1,4})/i.exec(v)}
function explicitIds(row){var out={tmdbId:"",imdbId:""};var tv=s(row&&(row.tmdbId||row.tmdb_id||row.tmdb));if(/^\d+$/.test(tv))out.tmdbId=tv;var iv=s(row&&(row.imdbId||row.imdb_id||row.imdb)).toLowerCase();if(/^tt\d+$/.test(iv))out.imdbId=iv;try{var u=new URL(s(row&&row.url)),qp=u.searchParams,t=s(qp.get("tmdbId")||qp.get("tmdb")||"");if(!out.tmdbId&&/^\d+$/.test(t))out.tmdbId=t;var i=s(qp.get("imdbId")||qp.get("imdb")||"").toLowerCase();if(!out.imdbId&&/^tt\d+$/.test(i))out.imdbId=i}catch(_e){}return out}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,episode:1,season:1,saison:1,stream:1,streaming:1,source:1,server:1,serveur:1,player:1,video:1,watch:1,play:1,direct:1,download:1,quality:1,unknown:1,fallback:1};var tech={vcloud:1,hubcloud:1,file:1,web:1,dl:1,webrip:1,webdl:1,bluray:1,remux:1,hdr:1,dv:1,dolby:1,atmos:1,aac:1,ac3:1,eac3:1,ddp:1,x264:1,x265:1,h264:1,h265:1,hevc:1,av1:1,multi:1,vf:1,vff:1,vfq:1,vostfr:1,vo:1,french:1,english:1,truefrench:1,hd:1,uhd:1,fhd:1,sd:1};var provider=norm(c.providerId).split(" ");return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!tech[x]&&provider.indexOf(x)<0&&!/^\d{4}$/.test(x)&&!/^\d{3,4}p$/.test(x)&&!/^s\d+e\d+$/.test(x)})}
function expectedTokens(m){var map={};uniq((m.titles||[]).concat(m.episodeTitles||[])).forEach(function(t){tokens(t).forEach(function(x){map[x]=1})});return map}
function overlapsExpected(text,expected){var w=tokens(text);for(var i=0;i<w.length;i++)if(expected[w[i]])return true;return false}
function explicitCandidates(row){var out=[],title=s(row&&row.title);if(title)out.push({text:title,kind:"title"});var filename=s(row&&row.filename);if(filename)out.push({text:filename,kind:"filename"});try{var base=decodeURIComponent(new URL(s(row&&row.url)).pathname.split("/").filter(Boolean).pop()||"").replace(/\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)$/i,"");if(base)out.push({text:base,kind:"url"})}catch(_e){}var name=s(row&&row.name);if(name&&norm(name)!==norm(c.providerId))out.push({text:name,kind:"name"});return out}
function contentLike(candidate){var w=tokens(candidate.text),se=episode(candidate.text),years=norm(candidate.text).match(/\b(?:19|20)\d{2}\b/g)||[];if(se)return true;if(years.length&&w.length>=1)return true;if((candidate.kind==="title"||candidate.kind==="filename")&&w.length>=3)return true;return false}
function queryTitle(text){return tokens(text).join(" ").trim()}
function strongNameMatch(query,result){var a=tokens(query),names=uniq([result&&result.name,result&&result.original_name,result&&result.title,result&&result.original_title]);if(a.length<2)return false;for(var n=0;n<names.length;n++){var b=tokens(names[n]);if(!b.length)continue;var hit=0;a.forEach(function(x){if(b.indexOf(x)>=0)hit++});var ratio=hit/Math.max(a.length,b.length);if(ratio>=0.67)return true}return false}
async function confirmOtherTitle(candidate,q){if(!/^\d+$/.test(q.tmdbId||""))return false;var query=queryTitle(candidate.text);if(tokens(query).length<2)return false;var endpoint=episodic(q)?"tv":"movie",d=await jsonFetch("https://api.themoviedb.org/3/search/"+endpoint+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&query="+encodeURIComponent(query)+"&include_adult=false");if(!d||!Array.isArray(d.results))return false;for(var i=0;i<Math.min(5,d.results.length);i++){var row=d.results[i];if(!strongNameMatch(query,row))continue;var id=s(row&&row.id);if(id===q.tmdbId)return false;return /^\d+$/.test(id)&&id!==q.tmdbId}return false}
async function candidateContradicts(candidate,q,m,expected){var text=candidate.text,se=episode(text);if(q.mediaType==="movie"&&se)return true;if(se&&episodic(q)){var ss=Number(se[1])||0,ee=Number(se[2])||0;if((q.season&&ss&&ss!==q.season)||(q.episode&&ee&&ee!==q.episode))return true;if(overlapsExpected(text,expected))return false;return await confirmOtherTitle(candidate,q)}var years=norm(text).match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&!years.some(function(y){return Math.abs(Number(y)-Number(m.year))<=1}))return true;if(!contentLike(candidate)||overlapsExpected(text,expected))return false;var w=tokens(text);if(w.length<2)return false;if(years.length)return true;if(w.length>=3&&(candidate.kind==="title"||candidate.kind==="filename"))return await confirmOtherTitle(candidate,q);return false}
async function mismatch(row,q,m){var ids=explicitIds(row);if(ids.tmdbId&&q.tmdbId&&ids.tmdbId!==q.tmdbId)return true;if(ids.imdbId&&(q.imdbId||m.imdbId)&&ids.imdbId!==(q.imdbId||m.imdbId))return true;var expected=expectedTokens(m),cands=explicitCandidates(row);for(var i=0;i<cands.length;i++)if(await candidateContradicts(cands[i],q,m,expected))return true;return false}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamIdentityV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var m=await tmdb(q),kept=[];for(var i=0;i<x.list.length;i++)if(!(await mismatch(x.list[i],q,m)))kept.push(x.list[i]);return rebuild(v,x,kept)};wrap.__nuvioGlobalStreamIdentityV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"einthusan","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"cross-client-positive-mismatch-anime-confirmed-v3"});
/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:ec3075fea877 */
;(function(g,c){"use strict";
function s(v){return String(v==null?"":v).trim()}
function meaningful(v){var x=s(v);return x&&!/^(?:unknown|inconnue?|n\/?a|null|undefined|none|-+)$/i.test(x)}
function uniq(a){var o=[];(a||[]).forEach(function(v){if(v&&o.indexOf(v)<0)o.push(v)});return o}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function req(a){var f=a[0],q=f&&typeof f==="object"&&!Array.isArray(f)?Object.assign({},f):{tmdbId:f,mediaType:a[1],season:a[2],episode:a[3]};q.tmdbId=s(q.tmdbId||q.id||f).replace(/^tmdb:/i,"").split(":")[0];q.mediaType=s(q.mediaType||q.type||a[1]||"movie").toLowerCase();q.title=s(q.title||q.name||q.label);q.year=Number(q.year||0)||0;q.season=Number(q.season||a[2]||0)||0;q.episode=Number(q.episode||a[3]||0)||0;return q}
function blob(r){return [r&&r.name,r&&r.title,r&&r.size,r&&r.description,r&&r.quality,r&&r.language,r&&r.codec,r&&r.audio,r&&r.sourceType,r&&r.releaseType,r&&r.format,r&&r.hdr,r&&r.videoTech,r&&r.bitDepth,r&&r.subtitles].map(s).join(" ")}
function quality(r){var v=meaningful(r&&r.quality)?s(r.quality):blob(r),u=v.toUpperCase();if(/(?:\b4K\b|\b2160P?\b|\bUHD\b)/.test(u))return"2160p";var m=u.match(/\b(1440|1080|720|576|540|480|360)P?\b/);return m?m[1]+"p":""}
function language(r){var v=meaningful(r&&r.language)?s(r.language):blob(r),u=v.toUpperCase();if(/\bMULTI(?:[- ]?AUDIO|LANG(?:UE)?S?)?\b/.test(u))return"Multi";if(/\bDUAL(?:[- ]?AUDIO)?\b/.test(u))return"Dual Audio";if(/\bVOSTFR\b/.test(u))return"VOSTFR";if(/\bVFQ\b/.test(u))return"VFQ";if(/\bVFF\b/.test(u))return"VFF";if(/\bVF\b/.test(u))return"VF";if(/\bVO\b/.test(u))return"VO";return meaningful(r&&r.language)?s(r.language):""}
function codec(r){var v=meaningful(r&&r.codec)?s(r.codec):blob(r),u=v.toUpperCase();if(/\b(?:HEVC|H[ ._-]?265|X265)\b/.test(u))return"HEVC";if(/\bAV1\b/.test(u))return"AV1";if(/\bVP9\b/.test(u))return"VP9";if(/\b(?:AVC|H[ ._-]?264|X264)\b/.test(u))return"AVC";return meaningful(r&&r.codec)?s(r.codec):""}
function audio(r){var v=meaningful(r&&r.audio)?s(r.audio):blob(r),u=v.toUpperCase(),ch="",cm=u.match(/\b(7\.1|5\.1|2\.1|2\.0)\b/);if(cm)ch=cm[1];var fmt="";if(/\b(?:ATMOS|DOLBY ATMOS)\b/.test(u))fmt="Dolby Atmos";else if(/\bTRUE[ ._-]?HD\b/.test(u))fmt="TrueHD";else if(/\b(?:E-?AC-?3|DDP|DD\+)\b/.test(u))fmt="E-AC3";else if(/\bAC-?3\b/.test(u))fmt="AC3";else if(/\bDTS[: ._-]?X\b/.test(u))fmt="DTS:X";else if(/\bDTS[- ]?HD\b/.test(u))fmt="DTS-HD";else if(/\bDTS\b/.test(u))fmt="DTS";else if(/\bAAC\b/.test(u))fmt="AAC";return{format:fmt||(meaningful(r&&r.audio)?s(r.audio):""),channels:ch}}
function duration(r){var raw=r&&r.duration;if(typeof raw==="number"&&Number.isFinite(raw)&&raw>0)return raw>600?Math.round(raw/60):Math.round(raw);var d=s(raw),m=d.match(/(\d{1,4})\s*(?:min|minutes?)\b/i);if(m)return Number(m[1]);var x=blob(r).match(/\b(\d{1,3})\s*(?:min|minutes?)\b/i);return x?Number(x[1]):0}
function source(r){var v=meaningful(r&&r.sourceType)?s(r.sourceType):blob(r),u=v.toUpperCase(),sourceType="",releaseType="";if(/\b(?:BLU[- ]?RAY|BDRIP|BRRIP|BDREMUX)\b/.test(u))sourceType="BLU-RAY";else if(/\bWEB[- .]?DL\b/.test(u))sourceType="WEB-DL";else if(/\bWEB[- .]?RIP\b/.test(u))sourceType="WEBRIP";else if(/\bHDTV\b/.test(u))sourceType="HDTV";else if(/\bDVD[- .]?RIP\b/.test(u))sourceType="DVD RIP";if(/\bREMUX\b/.test(u))releaseType="REMUX";return{sourceType:sourceType||(meaningful(r&&r.sourceType)?s(r.sourceType):""),releaseType:releaseType||(meaningful(r&&r.releaseType)?s(r.releaseType):"")}}
function formatType(r){var v=meaningful(r&&r.format)?s(r.format):"",u=v.toUpperCase();if(/(?:M3U8|HLS)/.test(u))return"HLS";if(/(?:MPD|DASH)/.test(u))return"DASH";if(/\bMP4\b/.test(u))return"MP4";if(/\bMKV\b/.test(u))return"MKV";var url=s(r&&r.url).split(/[?#]/)[0].toLowerCase();if(/\.m3u8$/.test(url))return"HLS";if(/\.mpd$/.test(url))return"DASH";if(/\.mp4$/.test(url))return"MP4";if(/\.mkv$/.test(url))return"MKV";return v}
function videoFacts(r){var u=blob(r).toUpperCase(),tech=[],bit="";if(/\b(?:DOLBY VISION|DOVI)\b/.test(u))tech.push("Dolby Vision");if(/\bHDR10\+\b|\bHDR10 PLUS\b/.test(u))tech.push("HDR10+");else if(/\bHDR10\b/.test(u))tech.push("HDR10");if(/\bIMAX[ ._-]?ENHANCED\b/.test(u))tech.push("IMAX Enhanced");else if(/\bIMAX\b/.test(u))tech.push("IMAX");if(/\b10[ ._-]?BIT\b|\bHI10P\b/.test(u))bit="10bit";else if(/\b8[ ._-]?BIT\b/.test(u))bit="8bit";return{tech:uniq(tech),bitDepth:bit}}
function subtitleFacts(r){var u=blob(r).toUpperCase(),out=[];if(/\bVOSTFR\b/.test(u))out.push("VOSTFR");if(/\bSUB[ ._-]?FR\b/.test(u))out.push("SUB FR");if(/\bSUB[ ._-]?EN\b/.test(u))out.push("SUB EN");if(/\bFORCED\b/.test(u))out.push("FORCED");if(/\bSDH\b/.test(u))out.push("SDH");return uniq(out)}
function age(r){var v=r&&(r.ageRating||r.certification);return meaningful(v)?s(v):""}
function providerName(r){var raw=meaningful(r&&r.name)?s(r.name):"",n=raw.split(/[|\n]/)[0].trim();if(n&&n.length<=40&&!/^(?:4k|2160p|1080p|720p|vf|vff|vfq|vostfr)$/i.test(n))return n;var id=s(c.providerId).replace(/[-_]+/g," ");return id?id.replace(/\b\w/g,function(x){return x.toUpperCase()}):"Source"}
function fileSize(r){var v=s(r&&r.size);if(!meaningful(v))return"";return /\b\d+(?:[.,]\d+)?\s*(?:KB|MB|GB|TB)\b/i.test(v)?v:""}
function badgeIds(f){var ids=[];var q={"2160p":"4k-ultra-hd","1080p":"1080p-full-hd","720p":"720p-hd","480p":"480p-sd"}[f.quality];if(q)ids.push(q);var src={"BLU-RAY":"blu-ray-disc","WEB-DL":"webdl","WEBRIP":"webrip","HDTV":"hdtv","DVD RIP":"dvd-rip"}[f.sourceType];if(src)ids.push(src);if(f.releaseType==="REMUX")ids.push("remux");f.videoTech.forEach(function(v){var id={"Dolby Vision":"dolby-vision","HDR10+":"hdr10-plus","HDR10":"hdr10","IMAX Enhanced":"imax-enhanced","IMAX":"imax"}[v];if(id)ids.push(id)});var co={"HEVC":"hevc","AVC":"avc"}[f.codec];if(co)ids.push(co);if(f.bitDepth)ids.push(f.bitDepth);var af={"Dolby Atmos":"dolby-atmos","TrueHD":"truehd","E-AC3":"dolby-digital-plus","AC3":"dolby-digital","DTS:X":"dts-x","DTS-HD":"dts-hd-ma"}[f.audioFormat];if(af)ids.push(af);if(f.audioChannels==="7.1")ids.push("7-1-audio");else if(f.audioChannels==="5.1")ids.push("5-1-audio");var lg={"Multi":"multi","VFF":"vff","VFQ":"vfq","VO":"vo","VOSTFR":"vostfr"}[f.language];if(lg)ids.push(lg);f.subtitles.forEach(function(v){var id={"VOSTFR":"vostfr","SUB FR":"sub-fr","SUB EN":"sub-en","FORCED":"forced","SDH":"sdh"}[v];if(id)ids.push(id)});return uniq(ids)}
function badgeLabels(f){var out=[];if(f.quality)out.push(f.quality==="2160p"?"4K":f.quality);if(f.sourceType)out.push(f.sourceType);if(f.releaseType)out.push(f.releaseType);out=out.concat(f.videoTech);if(f.codec)out.push(f.codec);if(f.bitDepth)out.push(f.bitDepth);if(f.audioFormat)out.push(f.audioFormat);if(f.audioChannels)out.push(f.audioChannels);if(f.language)out.push(f.language);out=out.concat(f.subtitles);if(f.duration)out.push(Math.floor(f.duration/60)?Math.floor(f.duration/60)+"h"+String(f.duration%60).padStart(2,"0"):f.duration+"min");if(f.ageRating)out.push(f.ageRating);return uniq(out)}
function nativeFetchBridge(){try{return !!(g&&typeof g.__native_fetch==="function")}catch(_e){return false}}
function safeSignal(){try{if(typeof AbortSignal!=="undefined"&&typeof AbortSignal.timeout==="function")return AbortSignal.timeout(c.tmdbTimeoutMs)}catch(_e){}return null}
function certification(d,kind){var rows=kind==="movie"?(d&&d.release_dates&&d.release_dates.results):(d&&d.content_ratings&&d.content_ratings.results);if(!Array.isArray(rows))return"";var row=rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="FR"})||rows.find(function(x){return s(x&&x.iso_3166_1).toUpperCase()==="US"})||rows[0];if(!row)return"";if(kind==="movie"){var releases=Array.isArray(row.release_dates)?row.release_dates:[];for(var i=0;i<releases.length;i++){var v=s(releases[i]&&releases[i].certification);if(v)return v}return""}return s(row.rating)}
async function tmdbJson(url){if(!g||typeof g.fetch!=="function")return null;var nativeBridge=nativeFetchBridge(),sig=nativeBridge?null:safeSignal();if(!nativeBridge&&!sig)return null;var init={headers:{Accept:"application/json"}};if(sig)init.signal=sig;try{var r=await g.fetch(url,init);if(!r||!r.ok)return null;return await r.json()}catch(_e){return null}}
async function tmdb(q){if(!/^\d+$/.test(q.tmdbId||""))return null;var kind=(q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"tv":"movie",append=kind==="movie"?"release_dates":"content_ratings",base="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId),d=await tmdbJson(base+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR&append_to_response="+append);if(!d)return null;var date=s(d.release_date||d.first_air_date),runtime=Number(d.runtime||0);if(!runtime&&Array.isArray(d.episode_run_time)&&d.episode_run_time.length)runtime=Number(d.episode_run_time[0]||0);var genres=Array.isArray(d.genres)?d.genres.map(function(x){return s(x&&x.name)}).filter(Boolean):[];var meta={title:s(d.title||d.name||q.title),year:Number((date.match(/(?:19|20)\d{2}/)||[])[0]||q.year||0)||0,runtime:runtime>0?Math.round(runtime):0,age:certification(d,kind),overview:s(d.overview),genres:genres,episodeTitle:"",episodeOverview:""};if(kind==="tv"&&q.season>0&&q.episode>0){var ep=await tmdbJson(base+"/season/"+encodeURIComponent(q.season)+"/episode/"+encodeURIComponent(q.episode)+"?api_key="+encodeURIComponent(c.tmdbKey)+"&language=fr-FR");if(ep){var er=Number(ep.runtime||0);if(er>0)meta.runtime=Math.round(er);meta.episodeTitle=s(ep.name);meta.episodeOverview=s(ep.overview)}}return meta}
function mediaLine(meta,q){var title=s((meta&&meta.title)||q.title),year=Number((meta&&meta.year)||q.year||0)||0,parts=[];if(title)parts.push(title);if(year)parts.push(String(year));if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0)){parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));if(meta&&meta.episodeTitle)parts.push(meta.episodeTitle)}return parts.join(" • ")}
function compact(meta,q){var title=s((meta&&meta.title)||q.title),parts=[];if(title)parts.push(title);if((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")&&(q.season>0||q.episode>0))parts.push("S"+String(q.season||0).padStart(2,"0")+"E"+String(q.episode||0).padStart(2,"0"));return parts.join(" • ")}
function present(r,meta,q){if(!r||typeof r!=="object")return r;var out=Object.assign({},r),au=audio(r),so=source(r),vf=videoFacts(r),f={quality:quality(r),language:language(r),codec:codec(r),audioFormat:au.format,audioChannels:au.channels,duration:duration(r)||(meta&&meta.runtime)||0,sourceType:so.sourceType,releaseType:so.releaseType,format:formatType(r),videoTech:vf.tech,bitDepth:vf.bitDepth,subtitles:subtitleFacts(r),ageRating:age(r)||(meta&&meta.age)||""};if(f.quality)out.quality=f.quality;if(f.language)out.language=f.language;if(f.codec)out.codec=f.codec;if(f.audioFormat)out.audio=f.audioFormat+(f.audioChannels?" "+f.audioChannels:"");if(f.duration)out.duration=f.duration;if(f.sourceType)out.sourceType=f.sourceType;if(f.releaseType)out.releaseType=f.releaseType;if(f.format)out.format=f.format;if(f.ageRating)out.ageRating=f.ageRating;out.badgeIds=badgeIds(f);out.displayBadges=badgeLabels(f);out.presentationFacts=f;var provider=providerName(r),media=mediaLine(meta,q),small=compact(meta,q),genres=meta&&Array.isArray(meta.genres)&&meta.genres.length?meta.genres.slice(0,3).join(", "):"",overview=s(meta&&((meta.episodeOverview)||meta.overview)),lines=[];if(media)lines.push(((q.mediaType==="tv"||q.mediaType==="series"||q.mediaType==="anime")?"📺 ":"🎬 ")+media+(genres?" • "+genres:""));if(overview)lines.push(overview);if(!lines.length)lines.push("🎬 "+provider);out.title=small?provider+" • "+small:provider;out.name=provider;out.description=lines.join("\n");var fs=fileSize(r);if(fs)out.size=fs;else if("size" in out)delete out.size;return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalStreamPresentationV1)return false;var native=o[k];var wrap=async function(){var q=req(arguments),v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var meta=null;try{meta=await tmdb(q)}catch(_e){}return rebuild(v,x,x.list.map(function(r){return present(r,meta,q)}))};wrap.__nuvioGlobalStreamPresentationV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports){ok=install(module.exports,"getStreams")||install(module.exports,"streams")}}catch(_e){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"einthusan","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"all-providers-facts-badge-dedupe-tmdb-fallback-v9"});
