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
})(typeof globalThis!=="undefined"?globalThis:this,[["YW5pbWVwYWhlLmNvbQ==","animepahe.pw"],["YW5pbWVwYWhlLm9yZw==","animepahe.pw"]]);
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */
;(function(g,encoded){
  if(!g||typeof g.fetch!=="function"||g.__nuvioAdaptiveDomainRecoveryV1)return;
  var nativeFetch=g.fetch.bind(g), groups=[];
  try{groups=JSON.parse(typeof atob==="function"?atob(encoded):Buffer.from(encoded,"base64").toString("utf8"));}catch(_e){return;}
  var cache=Object.create(null);
  function obsolete(status){return status===404||status===410||status===451||status===521||status===522||status===523;}
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
})(typeof globalThis!=="undefined"?globalThis:this,"W3siY2FuZGlkYXRlcyI6WyJodHRwczovL2FuaW1lcGFoZS5wdyJdLCJob3N0cyI6WyJhbmltZXBhaGUuY29tIl19LHsiY2FuZGlkYXRlcyI6WyJodHRwczovL2FuaW1lcGFoZS5wdyJdLCJob3N0cyI6WyJhbmltZXBhaGUub3JnIl19XQ==");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */

const _0x1d73f4=_0x3e95;(function(_0x59e55d,_0x1dbedb){const _0x18c825=_0x3e95,_0x510f3b=_0x59e55d();while(!![]){try{const _0x3d1169=parseInt(_0x18c825(0x1be))/0x1+parseInt(_0x18c825(0x1ba))/0x2*(parseInt(_0x18c825(0x1e5))/0x3)+-parseInt(_0x18c825(0x202))/0x4*(-parseInt(_0x18c825(0x1ec))/0x5)+-parseInt(_0x18c825(0x1f7))/0x6*(-parseInt(_0x18c825(0x1cb))/0x7)+parseInt(_0x18c825(0x1b7))/0x8+parseInt(_0x18c825(0x1d8))/0x9*(-parseInt(_0x18c825(0x1d1))/0xa)+parseInt(_0x18c825(0x213))/0xb*(-parseInt(_0x18c825(0x1f8))/0xc);if(_0x3d1169===_0x1dbedb)break;else _0x510f3b['push'](_0x510f3b['shift']());}catch(_0x15a0de){_0x510f3b['push'](_0x510f3b['shift']());}}}(_0x131e,0x6e357));var __create=Object[_0x1d73f4(0x1d3)],__defProp=Object[_0x1d73f4(0x1d6)],__defProps=Object[_0x1d73f4(0x1a9)],__getOwnPropDesc=Object['getOwnPropertyDescriptor'],__getOwnPropDescs=Object[_0x1d73f4(0x20e)],__getOwnPropNames=Object[_0x1d73f4(0x1fd)],__getOwnPropSymbols=Object[_0x1d73f4(0x1f2)],__getProtoOf=Object[_0x1d73f4(0x1ed)],__hasOwnProp=Object[_0x1d73f4(0x1dd)]['hasOwnProperty'],__propIsEnum=Object['prototype']['propertyIsEnumerable'],__defNormalProp=(_0x537b5d,_0x312257,_0x145bab)=>_0x312257 in _0x537b5d?__defProp(_0x537b5d,_0x312257,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x145bab}):_0x537b5d[_0x312257]=_0x145bab,__spreadValues=(_0x454d4c,_0x10c821)=>{const _0x1d55b3=_0x1d73f4;for(var _0x5ca226 in _0x10c821||(_0x10c821={}))if(__hasOwnProp[_0x1d55b3(0x214)](_0x10c821,_0x5ca226))__defNormalProp(_0x454d4c,_0x5ca226,_0x10c821[_0x5ca226]);if(__getOwnPropSymbols)for(var _0x5ca226 of __getOwnPropSymbols(_0x10c821)){if(__propIsEnum['call'](_0x10c821,_0x5ca226))__defNormalProp(_0x454d4c,_0x5ca226,_0x10c821[_0x5ca226]);}return _0x454d4c;},__spreadProps=(_0x3a8cb0,_0x2a9c46)=>__defProps(_0x3a8cb0,__getOwnPropDescs(_0x2a9c46)),__objRest=(_0x267409,_0x2a986e)=>{const _0x1f55b1=_0x1d73f4;var _0x4078ae={};for(var _0x37e51c in _0x267409)if(__hasOwnProp[_0x1f55b1(0x214)](_0x267409,_0x37e51c)&&_0x2a986e[_0x1f55b1(0x1ea)](_0x37e51c)<0x0)_0x4078ae[_0x37e51c]=_0x267409[_0x37e51c];if(_0x267409!=null&&__getOwnPropSymbols)for(var _0x37e51c of __getOwnPropSymbols(_0x267409)){if(_0x2a986e[_0x1f55b1(0x1ea)](_0x37e51c)<0x0&&__propIsEnum[_0x1f55b1(0x214)](_0x267409,_0x37e51c))_0x4078ae[_0x37e51c]=_0x267409[_0x37e51c];}return _0x4078ae;},__copyProps=(_0x257f25,_0x2649d8,_0xdbf521,_0x41706a)=>{const _0x4bd517=_0x1d73f4;if(_0x2649d8&&typeof _0x2649d8===_0x4bd517(0x212)||typeof _0x2649d8===_0x4bd517(0x1cf)){for(let _0x5e4956 of __getOwnPropNames(_0x2649d8))if(!__hasOwnProp[_0x4bd517(0x214)](_0x257f25,_0x5e4956)&&_0x5e4956!==_0xdbf521)__defProp(_0x257f25,_0x5e4956,{'get':()=>_0x2649d8[_0x5e4956],'enumerable':!(_0x41706a=__getOwnPropDesc(_0x2649d8,_0x5e4956))||_0x41706a[_0x4bd517(0x1c6)]});}return _0x257f25;},__toESM=(_0x55ba45,_0x23f426,_0x31a83c)=>(_0x31a83c=_0x55ba45!=null?__create(__getProtoOf(_0x55ba45)):{},__copyProps(_0x23f426||!_0x55ba45||!_0x55ba45['__esModule']?__defProp(_0x31a83c,_0x1d73f4(0x1b4),{'value':_0x55ba45,'enumerable':!![]}):_0x31a83c,_0x55ba45)),__async=(_0x1abd7c,_0x51d469,_0x4db3b0)=>{return new Promise((_0x1cb0f7,_0x58ba9a)=>{const _0x5006dd=_0x3e95;var _0x16f488=_0x2becae=>{const _0x4f80c0=_0x3e95;try{_0x3ddc4b(_0x4db3b0[_0x4f80c0(0x1b0)](_0x2becae));}catch(_0x4fff13){_0x58ba9a(_0x4fff13);}},_0x446bda=_0x2a96d8=>{try{_0x3ddc4b(_0x4db3b0['throw'](_0x2a96d8));}catch(_0x4ee400){_0x58ba9a(_0x4ee400);}},_0x3ddc4b=_0x28cd85=>_0x28cd85['done']?_0x1cb0f7(_0x28cd85[_0x5006dd(0x1ae)]):Promise[_0x5006dd(0x1ca)](_0x28cd85[_0x5006dd(0x1ae)])[_0x5006dd(0x1f6)](_0x16f488,_0x446bda);_0x3ddc4b((_0x4db3b0=_0x4db3b0[_0x5006dd(0x1fb)](_0x1abd7c,_0x51d469))[_0x5006dd(0x1b0)]());});},import_cheerio_without_node_native=__toESM(require(_0x1d73f4(0x1ff))),MAIN_URL=_0x1d73f4(0x207),PROXY_URL=_0x1d73f4(0x1c1),HEADERS={'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20Chrome/120.0.0.0\x20Safari/537.36','Cookie':_0x1d73f4(0x201),'Referer':_0x1d73f4(0x1e1)};function fetchText(_0x53d5e8){return __async(this,arguments,function*(_0x3a9d6b,_0x3f7815={}){const _0x22182a=_0x3e95,_0x263547=_0x3f7815,{useProxy:useProxy=!![]}=_0x263547,_0x5368ce=__objRest(_0x263547,[_0x22182a(0x20a)]),_0x3553fa=_0x3a9d6b[_0x22182a(0x1e3)](_0x22182a(0x1cd))?_0x3a9d6b:''+MAIN_URL+_0x3a9d6b,_0x23e259=useProxy?''+PROXY_URL+encodeURIComponent(_0x3553fa):_0x3553fa,_0x53e991=yield fetch(_0x23e259,__spreadValues({'headers':HEADERS},_0x5368ce));if(!_0x53e991['ok'])throw new Error('HTTP\x20'+_0x53e991[_0x22182a(0x1fc)]+_0x22182a(0x1c5)+_0x3553fa);return yield _0x53e991[_0x22182a(0x210)]();});}function fetchJson(_0xbe08be){return __async(this,arguments,function*(_0x290be1,_0x1fec65={}){const _0x6a80f1=_0x3e95,_0x562e16=yield fetchText(_0x290be1,_0x1fec65);return JSON[_0x6a80f1(0x1bd)](_0x562e16);});}function getImdbId(_0x34ed2f,_0x226466){return __async(this,null,function*(){const _0x404dbd=_0x3e95;try{const _0x42212d=_0x404dbd(0x1e6)+(_0x226466==='tv'?'tv':'movie')+'/'+_0x34ed2f+_0x404dbd(0x1b9),_0x49d3ef=yield fetch(_0x42212d),_0x28a7ea=yield _0x49d3ef[_0x404dbd(0x1bb)]();return _0x28a7ea[_0x404dbd(0x1ad)];}catch(_0x4cf7e7){return null;}});}function resolveMapping(_0x459472,_0x2cc631,_0x460b16){return __async(this,null,function*(){const _0x13788c=_0x3e95;try{const _0x130392=_0x13788c(0x1aa)+_0x459472+_0x13788c(0x1e2)+_0x2cc631+_0x13788c(0x1b5)+_0x460b16,_0x21e924=yield fetch(_0x130392);if(!_0x21e924['ok'])return null;return yield _0x21e924[_0x13788c(0x1bb)]();}catch(_0x2c2385){return null;}});}function getMalTitle(_0x30d391){return __async(this,null,function*(){const _0x15e96f=_0x3e95;try{const _0x4abe52=yield fetch(_0x15e96f(0x1c3)+_0x30d391);if(!_0x4abe52['ok'])return null;const _0x238ad3=yield _0x4abe52['json']();return _0x238ad3[_0x15e96f(0x1eb)][_0x15e96f(0x20f)];}catch(_0x263c9e){return null;}});}function searchAnime(_0x3fa230){return __async(this,null,function*(){const _0x346695='/api?m=search&l=8&q='+encodeURIComponent(_0x3fa230);return yield fetchJson(_0x346695);});}function _0x131e(){const _0x125331=['C3rHDhvZ','z2v0t3DUuhjVCgvYDhLoyw1LCW','rg9TywLUifnLBgvJDgLVBG','y2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzL','C2vZC2LVBG','x19KzgCYxZ0XmJm0nty3odKW','nZjdAMjWv0S','yw5PBwvWywHLlNb3','jNnVCNq9zxbPC29Kzv9HC2mMCgfNzt0X','B3jPz2LUywXFDgL0Bgu','w0fUAw1LugfOzv0Gs3DPAYbLEhrYywn0Aw9UigzHAwXLzdO','Ahr0Chm6lY9HBMLTzxbHAguUy29T','zxbPC29Kzq','C3bSAxq','DxnLuhjVEhK','qw5PBwvqywHLicG','p2fWAv9RzxK9mtG2nwy0m2eWntq5y2e1mgqZndfKzdLHyJHImJLMndK','BwLU','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','DgL0Bgu','Dgv4Da','Bwf0y2G','B2jQzwn0','nZq5mdm3m0rxExnwwG','y2fSBa','BwvZC2fNzq','zMXVB3i','zgvMAw5LuhjVCgvYDgLLCW','Ahr0Chm6lY9Pzc1TyxbWAw5NlwfWAs1TywXPzc5OzI5ZCgfJzs9HCgKVCMvZB2X2zt9Pzd0','qw5PBwvqywHLigzYzxf1zw50BhKGCM90yxrLCYbKB21HAw5ZlIbdAg9VC2uGDgHLig9UzsbJDxjYzw50BhKGD29YA2LUzYbMB3iGEw91lG','BxLHBMLTzwXPC3qUBMv0l2fUAw1LlW','Aw1KyL9Pza','DMfSDwu','C3vIC3rYAw5N','BMv4Da','C2vSzwn0','CxvHBgL0Eq','w0fUAw1LugfOzv0Gvw5WywnRigvYCM9YoG','zgvMyxvSDa','jMu9','Dg9tDhjPBMC','ntiZmdq3mLPTtwLQDq','Ahr0Chm6lY9HBMLTzxbHAguUB3jN','l2v4DgvYBMfSx2LKCZ9HCgLFA2v5pte4nJvMndnHmdu0ownHntbKmZqXzgq5ywi4yJi5zJq5','mtqYAfDyCMDz','ANnVBG','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmc4WlJaUmcbtywzHCMKVntm3lJm2','CgfYC2u','nJm3mZu2AxLVthHQ','ChvZAa','zg9TywLU','Ahr0Chm6lY9HBMLTzxbHAgvWCM94Es5WAgLZAgvYyw5PBwvWywHLlNDVCMTLCNmUzgv2lZ91CMW9','zxjYB3i','Ahr0Chm6lY9HCgKUAMLRyw4UBw9Ll3y0l2fUAw1LlW','nZiWCa','ig9Uia','zw51BwvYywjSzq','zMLUza','yw5PBwvWywHLlM9YzW','uhjLzMvYCMvKierVBwfPBG','CMvZB2X2zq','nZDIzvffsuq','zNjVBunOyxjdB2rL','Ahr0Ca','zxHWB3j0CW','zNvUy3rPB24','Ahr0Chm6lY9HBMLTzxbHAguUChC','mJK3mdi2mgXfq0DJqW','B25tzxr0Aw5NCW','y3jLyxrL','Dg9mB3DLCKnHC2u','ic0GrxbPC29Kzsa','zgvMAw5LuhjVCgvYDhK','ywXS','owXMCNnPAa','zxzHBcHMDw5JDgLVBIHWlgeSyYXRlguSzcK','l2fWAt9TpxjLBgvHC2uMAwq9','BgvUz3rO','Ahr0Chm6lY9RD2LRlMn4lW','ChjVDg90ExbL','Dw5KzwzPBMvK','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY9TB3zPzs8','l2fUAw1LlW','Ahr0Chm6lY9HBMLTzxbHAguUy29TlW','jNm9','C3rHCNrZv2L0Aa','rhvI','mJKWndLmt3bKDvK','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','BwfSx2vWAxnVzgu','y2vPBa','CMvWBgfJzq','Aw5KzxHpzG','zgf0yq','odC2ndv1s0rAsgy','z2v0uhjVDg90ExbLt2y','zwfJAa','i3jLC29SDxrPB25nzw51igj1DhrVBG','jNnVCNq9zxbPC29Kzv9HC2mMCgfNzt0','DxjS','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ','zw5N','Aw5JBhvKzxm','yxr0CG','DgHLBG','mJCXmtqWwfneEujU','mZzJuMLOANO','z2v0u3rYzwfTCW','A3DPAW','yxbWBhK'];_0x131e=function(){return _0x125331;};return _0x131e();}function _0x3e95(_0x225e7c,_0x4de307){_0x225e7c=_0x225e7c-0x1a9;const _0x131ed8=_0x131e();let _0x3e95ec=_0x131ed8[_0x225e7c];if(_0x3e95['LKpEfA']===undefined){var _0x374763=function(_0x19c5e3){const _0x3c1902='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x537b5d='',_0x312257='';for(let _0x145bab=0x0,_0x454d4c,_0x10c821,_0x5ca226=0x0;_0x10c821=_0x19c5e3['charAt'](_0x5ca226++);~_0x10c821&&(_0x454d4c=_0x145bab%0x4?_0x454d4c*0x40+_0x10c821:_0x10c821,_0x145bab++%0x4)?_0x537b5d+=String['fromCharCode'](0xff&_0x454d4c>>(-0x2*_0x145bab&0x6)):0x0){_0x10c821=_0x3c1902['indexOf'](_0x10c821);}for(let _0x3a8cb0=0x0,_0x2a9c46=_0x537b5d['length'];_0x3a8cb0<_0x2a9c46;_0x3a8cb0++){_0x312257+='%'+('00'+_0x537b5d['charCodeAt'](_0x3a8cb0)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x312257);};_0x3e95['InubeT']=_0x374763,_0x3e95['dfHCpH']={},_0x3e95['LKpEfA']=!![];}const _0x21fda7=_0x131ed8[0x0],_0x9dd59a=_0x225e7c+_0x21fda7,_0x297c24=_0x3e95['dfHCpH'][_0x9dd59a];return!_0x297c24?(_0x3e95ec=_0x3e95['InubeT'](_0x3e95ec),_0x3e95['dfHCpH'][_0x9dd59a]=_0x3e95ec):_0x3e95ec=_0x297c24,_0x3e95ec;}function extractQuality(_0x334f2a){const _0x382715=_0x1d73f4,_0x39fb17=_0x334f2a[_0x382715(0x211)](/(\d{3,4}p)/);return _0x39fb17?_0x39fb17[0x1]:_0x382715(0x1c4);}function unpack(_0xe31c41){const _0xdd0574=_0x1d73f4;try{const _0xb76ad=_0xe31c41[_0xdd0574(0x211)](/}\((['"])([\s\S]*?)\1,\s*(\d+),\s*(\d+),\s*(['"])([\s\S]*?)\5\.split\((['"])\|\7\)/);if(_0xb76ad){let [_0x5456ad,_0x1c0673,_0x51199a,_0x2f53c4,_0x8c4f7d,_0x2f8bea,_0x357743]=_0xb76ad;_0x51199a=_0x51199a['replace'](/\\'/g,'\x27')[_0xdd0574(0x1e9)](/\\"/g,'\x22')['replace'](/\\\\/g,'\x5c'),_0x2f53c4=parseInt(_0x2f53c4),_0x8c4f7d=parseInt(_0x8c4f7d);const _0x354b84=_0x357743[_0xdd0574(0x209)]('|'),_0x530bd9=_0x1ec9b0=>(_0x1ec9b0<_0x2f53c4?'':_0x530bd9(parseInt(_0x1ec9b0/_0x2f53c4)))+((_0x1ec9b0=_0x1ec9b0%_0x2f53c4)>0x23?String[_0xdd0574(0x1cc)](_0x1ec9b0+0x1d):_0x1ec9b0[_0xdd0574(0x1b6)](0x24)),_0x4b988a={};while(_0x8c4f7d--)_0x4b988a[_0x530bd9(_0x8c4f7d)]=_0x354b84[_0x8c4f7d]||_0x530bd9(_0x8c4f7d);return _0x51199a[_0xdd0574(0x1e9)](/\b\w+\b/g,_0x574c2b=>_0x4b988a[_0x574c2b]);}}catch(_0x2f2b57){console['error'](_0xdd0574(0x1b3),_0x2f2b57[_0xdd0574(0x215)]);}return _0xe31c41;}function extractKwik(_0x3437f3){return __async(this,null,function*(){const _0x28243d=_0x3e95;try{const _0x495ea4=globalThis['SCRAPER_SETTINGS']||{},_0x3cd98e=_0x495ea4['domain']||_0x28243d(0x207),_0x24d558=yield fetchText(_0x3437f3,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x3cd98e+'/','User-Agent':_0x28243d(0x1bc)}),'useProxy':![]}),_0x1c346c=_0x24d558['match'](/<script.*?>([\s\S]*?)<\/script>/g)||[],_0x12465c=[];for(const _0x15ba09 of _0x1c346c){if(_0x15ba09[_0x28243d(0x1f4)](_0x28243d(0x1d9))){let _0x21942c=0x0;while(!![]){const _0x34bf2f=_0x15ba09['indexOf'](_0x28243d(0x1d9),_0x21942c);if(_0x34bf2f===-0x1)break;const _0x338b30=_0x15ba09[_0x28243d(0x1ea)]('.split(\x27|\x27)',_0x34bf2f);if(_0x338b30===-0x1)break;const _0x3ddf3c=_0x15ba09['indexOf']('))',_0x338b30);if(_0x3ddf3c===-0x1)break;_0x12465c[_0x28243d(0x1bf)](_0x15ba09[_0x28243d(0x1af)](_0x34bf2f,_0x3ddf3c+0x2)),_0x21942c=_0x3ddf3c+0x2;}}}for(const _0x14c3ab of _0x12465c){const _0x235e1d=unpack(_0x14c3ab),_0x42fe27=_0x235e1d[_0x28243d(0x211)](/source\s*=\s*'([^']+m3u8[^']*)'/)||_0x235e1d[_0x28243d(0x211)](/source\s*=\s*"([^"]+m3u8[^"]*)"/);if(_0x42fe27)return{'url':_0x42fe27[0x1],'headers':{'Referer':_0x28243d(0x1dc),'Origin':'https://kwik.cx','User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/120.0.0.0\x20Safari/537.36'}};}}catch(_0x2c7b87){console[_0x28243d(0x1c2)](_0x28243d(0x206),_0x2c7b87[_0x28243d(0x215)]);}return null;});}function getStreams(_0x1a69bb,_0x2befb3,_0x52fcf8,_0xfc825d){return __async(this,null,function*(){const _0x205542=_0x3e95;try{let _0x5e5e45=null,_0x581fa6='',_0x2c186e=_0xfc825d,_0x18bb35=null;if(_0x2befb3==='tv'){const _0x324a65=yield getImdbId(_0x1a69bb,_0x2befb3);if(!_0x324a65)return[];const _0xd31fc=yield resolveMapping(_0x324a65,_0x52fcf8,_0xfc825d);if(!_0xd31fc||!_0xd31fc['mal_id'])return[];_0x18bb35=_0xd31fc['mal_id'],_0x2c186e=_0xd31fc[_0x205542(0x1e7)]||_0xfc825d,_0x581fa6=yield getMalTitle(_0x18bb35);if(!_0x581fa6)return[];const _0x4cf3da=yield searchAnime(_0x581fa6);if(_0x4cf3da[_0x205542(0x1eb)]&&_0x4cf3da[_0x205542(0x1eb)][_0x205542(0x1db)]>0x0)for(let _0x22ea5c=0x0;_0x22ea5c<Math[_0x205542(0x20d)](_0x4cf3da[_0x205542(0x1eb)][_0x205542(0x1db)],0x3);_0x22ea5c++){const _0x481763=_0x4cf3da[_0x205542(0x1eb)][_0x22ea5c],_0x1a4687=yield fetchText(_0x205542(0x1e0)+_0x481763[_0x205542(0x200)]);if(_0x1a4687[_0x205542(0x1f4)](_0x205542(0x1ac)+_0x18bb35)){_0x5e5e45=_0x481763[_0x205542(0x200)];break;}}}else{const _0x426da0=_0x205542(0x1df)+_0x1a69bb+_0x205542(0x20c),_0x51feb2=yield fetch(_0x426da0),_0xc37f69=yield _0x51feb2[_0x205542(0x1bb)]();_0x581fa6=_0xc37f69[_0x205542(0x20f)]||_0xc37f69[_0x205542(0x205)],_0x2c186e=0x1;if(!_0x581fa6)return[];const _0x1201c6=yield searchAnime(_0x581fa6);if(_0x1201c6[_0x205542(0x1eb)]&&_0x1201c6[_0x205542(0x1eb)]['length']>0x0){const _0xbe3fcd=_0x1201c6['data'][0x0];_0xbe3fcd['title'][_0x205542(0x1d4)]()===_0x581fa6[_0x205542(0x1d4)]()&&(_0x5e5e45=_0xbe3fcd['session']);}}if(!_0x5e5e45)return[];const _0xf57a00=_0x205542(0x1da)+_0x5e5e45+_0x205542(0x204),_0x2f7c8a=yield fetchJson(_0xf57a00);if(!_0x2f7c8a[_0x205542(0x1eb)]||_0x2f7c8a[_0x205542(0x1eb)][_0x205542(0x1db)]===0x0)return[];const _0x38a1e6=Math[_0x205542(0x216)](_0x2f7c8a['data'][0x0][_0x205542(0x208)]),_0x1712c9=_0x2f7c8a['per_page']||0x1e,_0x203dac=_0x38a1e6-0x1+_0x2c186e,_0x341dc5=Math[_0x205542(0x1e8)](_0x2c186e/_0x1712c9)||0x1,_0x2b765d=_0x205542(0x1da)+_0x5e5e45+_0x205542(0x1f0)+_0x341dc5,_0x2a1326=yield fetchJson(_0x2b765d);let _0x55ba83=null;if(_0x2a1326&&_0x2a1326[_0x205542(0x1eb)]){const _0x34b42a=_0x2a1326['data']['find'](_0x1c811c=>Math[_0x205542(0x216)](_0x1c811c[_0x205542(0x208)])==_0x203dac);if(_0x34b42a)_0x55ba83=_0x34b42a[_0x205542(0x200)];}if(!_0x55ba83&&_0x341dc5!==0x1){const _0x2d7354=_0x2f7c8a[_0x205542(0x1eb)][_0x205542(0x1c7)](_0x213fbf=>Math[_0x205542(0x216)](_0x213fbf['episode'])==_0x203dac);if(_0x2d7354)_0x55ba83=_0x2d7354[_0x205542(0x200)];}if(!_0x55ba83)return[];const _0x418b69='/play/'+_0x5e5e45+'/'+_0x55ba83,_0x1219db=yield fetchText(_0x418b69),_0x50d5e1=import_cheerio_without_node_native['default']['load'](_0x1219db),_0xf83878=[],_0x3369fd=[];_0x50d5e1(_0x205542(0x1ef))[_0x205542(0x1ee)]((_0x48d682,_0x3a3741)=>{const _0x32e31e=_0x205542,_0xe51f28=_0x50d5e1(_0x3a3741),_0x4d5d8e=_0xe51f28[_0x32e31e(0x1f5)]('data-src'),_0x22e454=_0xe51f28[_0x32e31e(0x210)](),_0x22d1e4=extractQuality(_0x22e454),_0x1e1048=_0x22e454[_0x32e31e(0x1d4)]()[_0x32e31e(0x1f4)](_0x32e31e(0x1f3))?_0x32e31e(0x1e4):'Sub';_0x4d5d8e&&_0x4d5d8e[_0x32e31e(0x1f4)](_0x32e31e(0x1fa))&&_0x3369fd[_0x32e31e(0x1bf)](extractKwik(_0x4d5d8e)[_0x32e31e(0x1f6)](_0x126da6=>{const _0x41c033=_0x32e31e;_0x126da6&&_0xf83878['push']({'name':_0x41c033(0x20b)+_0x22d1e4+'\x20'+_0x1e1048+')','title':_0x581fa6+_0x41c033(0x1d5)+_0x2c186e,'url':_0x126da6[_0x41c033(0x1f1)],'quality':_0x22d1e4,'headers':_0x126da6['headers']});}));}),yield Promise[_0x205542(0x1d7)](_0x3369fd);const _0x33e14a={'1080p':0x3,'720p':0x2,'360p':0x1};return _0xf83878['sort']((_0x45ffbb,_0x54b2c9)=>(_0x33e14a[_0x54b2c9[_0x205542(0x1b2)]]||0x0)-(_0x33e14a[_0x45ffbb['quality']]||0x0));}catch(_0x18cd2a){return[];}});}function onSettings(){return __async(this,null,function*(){const _0x5ece5c=_0x3e95;return[{'type':'header','label':_0x5ece5c(0x1fe)},{'type':_0x5ece5c(0x1b1),'key':_0x5ece5c(0x1c0),'label':_0x5ece5c(0x1c9),'description':_0x5ece5c(0x1ab),'options':[{'label':'animepahe.pw','value':'https://animepahe.pw'},{'label':_0x5ece5c(0x1c8),'value':_0x5ece5c(0x1b8)},{'label':_0x5ece5c(0x203),'value':_0x5ece5c(0x1d0)}],'defaultValue':'https://animepahe.pw'}];});}typeof module!==_0x1d73f4(0x1de)&&module[_0x1d73f4(0x1ce)]?module[_0x1d73f4(0x1ce)]={'getStreams':getStreams,'onSettings':onSettings}:(global[_0x1d73f4(0x1f9)]=getStreams,global[_0x1d73f4(0x1d2)]=onSettings);

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
