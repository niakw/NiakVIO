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
})(typeof globalThis!=="undefined"?globalThis:this,[["bW92aWVzbW9kLm1vbmV5","moviesmod.zone"]]);
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
})(typeof globalThis!=="undefined"?globalThis:this,"eyJncm91cHMiOlt7ImNhbmRpZGF0ZXMiOlsiaHR0cHM6Ly9tb3ZpZXNtb2QuYXJteSJdLCJob3N0cyI6WyJtb3ZpZXNtb2QubW9uZXkiXX1dLCJyZXZpc2lvbiI6InJldHJ5LXRyYW5zaWVudC12MiJ9");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */
const _0x51a88a=_0x16d2;(function(_0x116c9f,_0x2be7c6){const _0x164a46=_0x16d2,_0x582f61=_0x116c9f();while(!![]){try{const _0x1280c2=parseInt(_0x164a46(0x280))/0x1*(-parseInt(_0x164a46(0x1c0))/0x2)+parseInt(_0x164a46(0x2a0))/0x3*(-parseInt(_0x164a46(0x208))/0x4)+-parseInt(_0x164a46(0x28b))/0x5*(parseInt(_0x164a46(0x206))/0x6)+parseInt(_0x164a46(0x1bc))/0x7+-parseInt(_0x164a46(0x22b))/0x8*(parseInt(_0x164a46(0x1e6))/0x9)+-parseInt(_0x164a46(0x232))/0xa*(-parseInt(_0x164a46(0x212))/0xb)+-parseInt(_0x164a46(0x262))/0xc*(-parseInt(_0x164a46(0x216))/0xd);if(_0x1280c2===_0x2be7c6)break;else _0x582f61['push'](_0x582f61['shift']());}catch(_0x289d58){_0x582f61['push'](_0x582f61['shift']());}}}(_0x3ec3,0x81335));var __defProp=Object[_0x51a88a(0x231)],__defProps=Object[_0x51a88a(0x294)],__getOwnPropDescs=Object[_0x51a88a(0x1c4)],__getOwnPropSymbols=Object[_0x51a88a(0x1db)],__hasOwnProp=Object[_0x51a88a(0x255)]['hasOwnProperty'],__propIsEnum=Object[_0x51a88a(0x255)][_0x51a88a(0x201)],__defNormalProp=(_0x381050,_0x2f25e5,_0x2f5ccc)=>_0x2f25e5 in _0x381050?__defProp(_0x381050,_0x2f25e5,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x2f5ccc}):_0x381050[_0x2f25e5]=_0x2f5ccc,__spreadValues=(_0x4ae141,_0x47430b)=>{const _0x216502=_0x51a88a;for(var _0x2e402a in _0x47430b||(_0x47430b={}))if(__hasOwnProp[_0x216502(0x271)](_0x47430b,_0x2e402a))__defNormalProp(_0x4ae141,_0x2e402a,_0x47430b[_0x2e402a]);if(__getOwnPropSymbols)for(var _0x2e402a of __getOwnPropSymbols(_0x47430b)){if(__propIsEnum[_0x216502(0x271)](_0x47430b,_0x2e402a))__defNormalProp(_0x4ae141,_0x2e402a,_0x47430b[_0x2e402a]);}return _0x4ae141;},__spreadProps=(_0x518325,_0x34f9eb)=>__defProps(_0x518325,__getOwnPropDescs(_0x34f9eb)),__async=(_0x47ae1f,_0x40d275,_0x799fd8)=>{return new Promise((_0x4315b4,_0x1d0a5c)=>{const _0x3a7f47=_0x16d2;var _0x8d0541=_0x1cda47=>{const _0x95a227=_0x16d2;try{_0x48ddfb(_0x799fd8[_0x95a227(0x1cf)](_0x1cda47));}catch(_0x5392f9){_0x1d0a5c(_0x5392f9);}},_0x194c3f=_0x3a1559=>{const _0xfd683a=_0x16d2;try{_0x48ddfb(_0x799fd8[_0xfd683a(0x22d)](_0x3a1559));}catch(_0x2a7323){_0x1d0a5c(_0x2a7323);}},_0x48ddfb=_0x3be7b7=>_0x3be7b7[_0x3a7f47(0x24d)]?_0x4315b4(_0x3be7b7[_0x3a7f47(0x26d)]):Promise['resolve'](_0x3be7b7[_0x3a7f47(0x26d)])['then'](_0x8d0541,_0x194c3f);_0x48ddfb((_0x799fd8=_0x799fd8[_0x3a7f47(0x284)](_0x47ae1f,_0x40d275))[_0x3a7f47(0x1cf)]());});},cheerio=require('cheerio-without-node-native');console[_0x51a88a(0x251)](_0x51a88a(0x259));function _0x16d2(_0x194696,_0x442649){_0x194696=_0x194696-0x1ba;const _0x3ec371=_0x3ec3();let _0x16d255=_0x3ec371[_0x194696];if(_0x16d2['hmPewJ']===undefined){var _0x7486c=function(_0x4d4345){const _0xf7c5cc='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x381050='',_0x2f25e5='';for(let _0x2f5ccc=0x0,_0x4ae141,_0x47430b,_0x2e402a=0x0;_0x47430b=_0x4d4345['charAt'](_0x2e402a++);~_0x47430b&&(_0x4ae141=_0x2f5ccc%0x4?_0x4ae141*0x40+_0x47430b:_0x47430b,_0x2f5ccc++%0x4)?_0x381050+=String['fromCharCode'](0xff&_0x4ae141>>(-0x2*_0x2f5ccc&0x6)):0x0){_0x47430b=_0xf7c5cc['indexOf'](_0x47430b);}for(let _0x518325=0x0,_0x34f9eb=_0x381050['length'];_0x518325<_0x34f9eb;_0x518325++){_0x2f25e5+='%'+('00'+_0x381050['charCodeAt'](_0x518325)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x2f25e5);};_0x16d2['essIHH']=_0x7486c,_0x16d2['elsfNP']={},_0x16d2['hmPewJ']=!![];}const _0x2c5718=_0x3ec371[0x0],_0x4cf7ce=_0x194696+_0x2c5718,_0x1cd870=_0x16d2['elsfNP'][_0x4cf7ce];return!_0x1cd870?(_0x16d255=_0x16d2['essIHH'](_0x16d255),_0x16d2['elsfNP'][_0x4cf7ce]=_0x16d255):_0x16d255=_0x1cd870,_0x16d255;}function escapeRegExp(_0x48caf8){const _0x35faa1=_0x51a88a;return _0x48caf8[_0x35faa1(0x25d)](/[.*+?^${}()|[\]\\]/g,_0x35faa1(0x268));}var TMDB_API_KEY=_0x51a88a(0x26a),FALLBACK_DOMAIN='https://moviesmod.army',DOMAIN_CACHE_TTL=0x4*0x3c*0x3c*0x3e8,moviesModDomain=FALLBACK_DOMAIN,domainCacheTimestamp=0x0;function getMoviesModDomain(){return __async(this,null,function*(){const _0x59baa8=_0x16d2,_0xc92004=Date[_0x59baa8(0x25c)]();if(_0xc92004-domainCacheTimestamp<DOMAIN_CACHE_TTL)return moviesModDomain;try{console[_0x59baa8(0x251)]('[MoviesMod]\x20Fetching\x20latest\x20domain...');const _0x5409c4=yield fetch(_0x59baa8(0x29d),{'method':'GET','headers':{'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36'}});if(_0x5409c4['ok']){const _0x184e88=yield _0x5409c4['json']();_0x184e88&&_0x184e88['moviesmod']&&(moviesModDomain=_0x184e88[_0x59baa8(0x226)],domainCacheTimestamp=_0xc92004,console[_0x59baa8(0x251)](_0x59baa8(0x1e3)+moviesModDomain));}}catch(_0x1d49ea){console['error'](_0x59baa8(0x1d1)+_0x1d49ea[_0x59baa8(0x215)]);}return moviesModDomain;});}function _0x3ec3(){const _0x3940b2=['ic0+ia','ytPJB250ywLUCYGIuMvZDw1LienSB3vKiIK','mtjrr016CKm','zxHWB3j0CW','mti0uLn1B3bp','zwfJAa','Aw5WDxrBBMfTzt0Ix3DWx2H0DhaIxq','ChjPB3jPDhK','ic0Gy29UDgLUDwLUzY4UlG','w01VDMLLC01Vzf0GrxjYB3iGCMvZB2X2Aw5NierYAxzLC2vLzcbSAw5RoIa','Aw5JBhvKzxm','ihrVDgfSigXPBMTZ','tI9b','w01VDMLLC01Vzf0GrxjYB3iGCMvZB2X2Aw5NifjLC3vTzsbdBg91zcbSAw5RoIa','mZe5DLvOzfrs','BgLUA3mUBw9KChjVlMjSB2C','CxvHBgL0Eq','BwvZC2fNzq','mJi4nJG3mJLOq3bWug4','vKfmsuq','u2L6zsa6','w01VDMLLC01Vzf0GuMf3ihn0CMvHBxmGyMvMB3jLigzPBhrLCMLUzZOG','zMLSDgvY','AhjLzG','lNrPBwvKlwnVBNrLBNqTy2XPzw50x3nOB3DFmf81xZaGyq','w01VDMLLC01Vzf0Gu3rYzwfTCYbHzNrLCIbUDwXSigzPBhrLCMLUzZOG','w01VDMLLC01Vzf0Gu3vJy2vZC2z1BgX5ihbYB2nLC3nLzca','w01VDMLLC01Vzf0GvgL0BguGBwf0y2GGzM91BMqSigj1Dcb5zwfYig1PC21HDgnOlIbnyxrJAgvKoIaI','C3rHDhvZ','w01VDMLLC01Vzf0GrMfSBgLUzYbIywnRihrVihrPDgXLihnLyxjJAcbMB3i6ia','w01VDMLLC01Vzf0GrM91BMqG','ytPJB250ywLUCYGIq2XVDwqGuMvZDw1LierVD25SB2fKiIK','yNL0zxm9mc0X','w01VDMLLC01Vzf0Gq291BgqGBM90igzPBMqGzw5JB2rLzcbvuKWGAw4GBw9KCMvMzxiUAw4GBgLUAY4','Bw92AwvZBw9K','C3vIC3rYAw5N','Dgv4Da','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZKXlJaUndq3mI4XmJqGu2fMyxjPlZuZnY4ZnG','igXPBMTZigzYB20G','odi0CgDABMDh','w01VDMLLC01Vzf0Gu2TPChbPBMCGzxbPC29Kzsa','DgHYB3C','CMf0Aw5N','iIbPCYaI','ic0G','zgvMAw5LuhjVCgvYDhK','mZi5mZbNs2P0DLq','lcb1CMW9','C2vYDMvY','w01VDMLLC01Vzf0GvMfSAwrHDgLUzYbvuKW6ia','w01VDMLLC01Vzf0GqMvZDcbTyxrJAcbMB3iGiG','w01VDMLLC01Vzf0G','uMvZDw1LienSB3vK','C2vHC29U','y2XVDwqUDw5IBg9JA2vKz2fTzxmUD29YBgq','AgvHzgvYCW','w01VDMLLC01Vzf0GtM8Gzg93BMXVywqGBgLUA3mGzM91BMq','zMLYC3q','icbB','lNrOzwnVBNrLBNq','iIWGrxHWzwn0zwqGEwvHCJOG','yvTOCMvMkJ0IzhjPDMvZzwvKlM9YzYjDlcbHw2HYzwyQpsjJBg91zc51BMjSB2nRzwrNyw1LCY53B3jSzcjDlcbHw2HYzwyQpsj0zwnOlMnYzwf0AxzLzxHWCMvZC2LVBNnIBg9NlMnVBsjDlcbHw2HYzwyQpsj0zwnOlMv4yw16y3vSDhvYzs5PBIjD','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmc4WlJaUmcbtywzHCMKVntm3lJm2','w01VDMLLC01Vzf0GrM91BMqGzgLYzwn0igXPBMS6ia','Aw5WDxrBBMfTzt0Ix3DWx2H0DhaYiL0','w01VDMLLC01Vzf0GrxjYB3iGChjVy2vZC2LUzYbSAw5Ria','iIaO','qwX0zxjUyxrPDMuGrg93BMXVywq','D29YA2vY','B3jPz2LU','rg93BMXVywqGtgLUAW','DgvZDa','z3PPCcWGzgvMBgf0zq','zg9Uzq','iIb3AxrOigeGCMf0Aw5Nig9Mia','DgvJAc5LEgfTzgvNCMvLlNnPDgu','i2XHBMrPBMC','Bg9N','A2vLCc1HBgL2zq','w01VDMLLC01Vzf0Gve1eqIbjBMzVoIaI','icbBu0LexsbfCNjVCJOGq291BgqGBM90igzPBMqGBwv0ysbYzwzYzxnOihrHzYb3AxrOierYAxzLBgvLy2GGvvjmlG','ChjVDg90ExbL','yxr0CG','icbBu0LexsbfCNjVCJOGq291BgqGBM90igzPBMqGDMvYAwzPy2f0Aw9UigzVCM0U','w01VDMLLC01Vzf0GtM8GCMvSzxzHBNqGBgLUA3mGzM91BMqGywz0zxiGzMLSDgvYAw5N','w01VDMLLC01Vzf0GvxnPBMCGy2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzLigzVCIbet00GCgfYC2LUzW','jMfWCgvUzf90B19YzxnWB25Zzt1LEhrLCM5HBf9Pzhm','zxjYB3i','BM93','CMvWBgfJzq','w01VDMLLC01Vzf0GsfrntcbSzw5NDgG6ia','C3rYzwfT','lZ9Zpq','w01VDMLLC01Vzf0GtM8GzMLUywWGBgLUA3mGzM91BMqGzM9Yia','mtjdD2zrAhC','Ahr0Chm6lY9KCML2zxnLzwqUB3jN','Dgv4Dc9ODg1SlgfWCgXPy2f0Aw9Ul3HODg1Sk3HTBcXHChbSAwnHDgLVBI94BwW7Ct0WlJKSAw1Hz2uVD2vICcWQlYO7Ct0WlJG','CMvZDw1L','C2vYAwvZ','Aw1KyL9Pza','xcqM','z2vUzxjPyW','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','DgvJAc5JCMvHDgL2zwv4ChjLC3nPB25ZyMXVzY5JB20','zxH0zxjUywXFAwrZ','DMfSDwu','C3rHDhvZvgv4Da','C29YDa','w01VDMLLC01Vzf0GvvjmihzHBgLKyxrPB246ifnvq0nfu1m','y2fSBa','l2fWAq','Dg9mB3DLCKnHC2u','AdmSigG0','C2vHCMnOugfYyw1Z','C3bSAxq','Aw5WDxrBBMfTzt0IDg9Rzw4Ixq','w01VDMLLC01Vzf0GtM8GDgLTzwqGy29UDgvUDcbMB3vUzcWGBg9VA2LUzYbMB3iGzgLYzwn0igXPBMTZlI4U','DhjPBq','BMv4DfvUDgLS','Ahr0Chm6lY9KCML2zxnLzwqUB3jNlW','w01VDMLLC01Vzf0GuMvZB2X2Aw5NifnjrcbSAw5RoIa','lMvUDhj5lwnVBNrLBNqGyvTOCMvMkJ0IzhjPDMvZzwvKlM9YzYjDlcaUzw50CNKTy29UDgvUDcbHw2HYzwyQpsjJBg91zc51BMjSB2nRzwrNyw1LCY53B3jSzcjDlcaUzw50CNKTy29UDgvUDcbHw2HYzwyQpsj0zwnOlMnYzwf0AxzLzxHWCMvZC2LVBNnIBg9NlMnVBsjDlcaUzw50CNKTy29UDgvUDcbHw2HYzwyQpsj0zwnOlMv4yw16y3vSDhvYzs5PBIjD','Bg9Hza','DMfS','ouzUufPbra','Bw92Awu','C2vHC29Uia','DgL0Bgu','yxbWBhK','q291BgqGBM90igv4DhjHy3qGDgL0BguGzNjVBsbuturcihjLC3bVBNnL','z2v0','B3b0Aw9UCZ0','w01VDMLLC01Vzf0Gu2vHCMnOAw5NoIa','Cg9ZDhmUBw9KChjVlMjSB2C','ANnVBG','mJiWnJa5nxvwsMXJAa','w01VDMLLC01Vzf0GuhjVy2vZC2LUzYbSAw5RoIbZzxj2zxi9iG','w01VDMLLC01Vzf0Gu2vSzwn0zwq6ia','CgfKu3rHCNq','DgvJAc5LEgfTEMn1Bhr1CMuUAw4','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','zg93BMXVywrpChrPB25Z','Adm6y29UDgfPBNmOiLnLyxnVBIiPlcbOna','iIWGCMvXDwvZDgvKigvWAxnVzgu9','zgvMAw5LuhjVCgvYDgLLCW','BMfTzq','w01VDMLLC01Vzf0GuhjVy2vZC2LUzYbKCML2zxnLzwqGvvjmoIa','w01VDMLLC01Vzf0GrhjPDMvZzwvKigLUzM86ia','icHUB3qGzxbPC29Kzsa','ue9tva','sfruuca','w01VDMLLC01Vzf0Grg93BMXVywqGB3b0Aw9UCYbHDMfPBgfIBgu6ia','Bwv0yvTODhrWlwvXDwL2psjYzwzYzxnOiL0','Ahr0Chm6lY9YyxCUz2L0AhvIDxnLCMnVBNrLBNqUy29Tl3bOAxnOzxi5oc9uvLzwvI9YzwzZl2HLywrZl21HAw4Vzg9TywLUCY5QC29U','C2vHCMnO','Bwf0y2G','mte4odLPt1vzv1C','icbBu0LexsbfCNjVCIbKDxjPBMCGu0LeihjLC29SDxrPB246ia','zM9YrwfJAa','mZq4mde2ow1rC1LIqW','lIbeAxnJyxjKAw5Nig1HDgnOlG','yMf0y2G','y29UDgvUDa','nte3mNDxAvfHAW','zhjPDMvZzwvKlM9YzW','Dg9gAxHLza','A2v5CW','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','z290ifvsta','lMXHDgvZDfbVC3q','w01VDMLLC01Vzf0GrxjYB3iGAw4Gz2v0u3rYzwfTCZOG','zMLUza','BgvUz3rO','vw5RBM93BG','Dg9tDhjPBMC','lcbMB3vUzcbLCgLZB2rLpq','DhLWzq','Bwf4','BMv4Da','p2fWAv9RzxK9','w01VDMLLC01Vzf0GrMfPBgvKihrVigzLDgnOigXHDgvZDcbKB21HAw46ia','yMvZDe1HDgnOsw5KzxG','zxbPC29KzsbSAw5RCW','CMvSzwfZzv9KyxrL','w01VDMLLC01Vzf0GrxjYB3iGC2vHCMnOAw5NoIa','w01VDMLLC01Vzf0Gsw5ZDgfUDcbbueKGCMvZDwX0oIa','w01VDMLLC01Vzf0GtM8GC2vHCMnOihjLC3vSDhmGzM91BMq','ywn0Aw9U','z2v0u3rYzwfTCW','ksbMB3iG','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ','w01VDMLLC01Vzf0Gsw5ZDgfUDcbMywXSyMfJAZOGDxnPBMCGvvjmigrPCMvJDgX5','ksbBsu1eqJOG','ChvZAa','w01VDMLLC01Vzf0GrxjYB3iGCMvZB2X2Aw5NifzPzgvVu2vLzcbSAw5RoIa','C29Tzq','w01VDMLLC01Vzf0GrM91BMqGBwf0y2GGDxnPBMCGsu1eqIbjrdOG','lI4U','w01VDMLLC01Vzf0GvxbKyxrLzcbKB21HAw4GDg86ia','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2','Ahr0Ca','nJKZodfsv2D3zeG','ihnLyxjJAcbYzxn1BhrZ','w01VDMLLC01Vzf0G4PYxifvstcb2ywXPzgf0Aw9UigzHAwXLzcb3AxrOihn0yxr1CZOG','ihjLDhvYBMvKigLUDMfSAwqGvvjm','rxbPC29Kzsa','yxbWBgLJyxrPB24VEc13D3CTzM9YBs11CMXLBMnVzgvK','w01VDMLLC01Vzf0Gvhj5Aw5NieLnreiGsuqGC2vHCMnOigzPCNn0oIa','ndGWCa','w01VDMLLC01Vzf0GtM8GC3vPDgfIBguGC2vHCMnOihjLC3vSDcbMB3vUzcbMB3iGiG','yNv0Dg9UlcaUzg93BMXVywqTyNrUlcaUyNrUlcbBy2XHC3mQpsjKB3DUBg9HzcjDlcbBy2XHC3mQpsjIDg4Ixq','DxjS','w01VDMLLC01Vzf0G4PYtifn1y2nLC3nMDwXSEsbYzxnVBhzLzcb1C2LUzYa','w01VDMLLC01Vzf0GuhjVy2vZC2LUzYbLCgLZB2rLia','zw4TvvmSzw47Ct0WlJu','uMvZDw1LifDVCMTLCIbcB3q','Ag9ZDg5HBwu','yvTOCMvMkJ0Il2rVD25SB2fKlYjD','Aw5ZDgfUDa','BNvSBa','tw92AwvZtw9Kia','Aw5KzxHpzG','w01VDMLLC01Vzf0GrxjYB3iGzxH0CMfJDgLUzYbKB3DUBg9HzcbSAw5RCZOG','zxbPC29KzxmUBw9KChjVlMjSB2C','C3rHCNrZv2L0Aa','ihn0CMvHBxm','yMvZDe1HDgnO','BwfW','ChjVCgvYDhLjC0vUDw1LCMfIBgu','w01VDMLLC01Vzf0GrxjYB3iGCMvZB2X2Aw5NigLUDgvYBwvKAwf0zsbSAw5RoIa','sw5ZDgfUDcbeB3DUBg9Hza'];_0x3ec3=function(){return _0x3940b2;};return _0x3ec3();}function makeRequest(_0x1ae0fe){return __async(this,arguments,function*(_0x199482,_0x5199b3={}){const _0x1429d6=_0x16d2,_0x2bd609={'User-Agent':_0x1429d6(0x229),'Accept':_0x1429d6(0x264),'Accept-Language':_0x1429d6(0x1f3),'Accept-Encoding':_0x1429d6(0x24c),'Connection':_0x1429d6(0x252),'Upgrade-Insecure-Requests':'1'},_0x450951=yield fetch(_0x199482,__spreadProps(__spreadValues({},_0x5199b3),{'headers':__spreadValues(__spreadValues({},_0x2bd609),_0x5199b3[_0x1429d6(0x23b)])}));if(!_0x450951['ok'])throw new Error(_0x1429d6(0x29a)+_0x450951[_0x1429d6(0x220)]+':\x20'+_0x450951[_0x1429d6(0x26e)]);return _0x450951;});}function extractQuality(_0x1b9902){const _0x25b6ff=_0x51a88a;if(!_0x1b9902)return'Unknown';const _0x5a9689=_0x1b9902[_0x25b6ff(0x29f)](/(480p|720p|1080p|2160p|4k)/i);if(_0x5a9689)return _0x5a9689[0x1];const _0x835a1c=_0x1b9902[_0x25b6ff(0x29f)](/(480p|720p|1080p|2160p|4k)[^)]*\)/i);if(_0x835a1c)return _0x835a1c[0x0];return _0x25b6ff(0x1ca);}function parseQualityForSort(_0x2b4bae){const _0x2997fe=_0x51a88a;if(!_0x2b4bae)return 0x0;const _0x49cac7=_0x2b4bae[_0x2997fe(0x29f)](/(\d{3,4})p/i);return _0x49cac7?parseInt(_0x49cac7[0x1],0xa):0x0;}function findBestMatch(_0x1c0839,_0x3fc62a){const _0x305427=_0x51a88a;if(!_0x3fc62a||_0x3fc62a[_0x305427(0x1c9)]===0x0)return{'bestMatch':{'target':'','rating':0x0},'bestMatchIndex':-0x1};const _0x9d106d=_0x3fc62a[_0x305427(0x200)](_0x5640a1=>{const _0x4b8289=_0x305427;if(!_0x5640a1)return 0x0;const _0x317d0c=_0x1c0839[_0x4b8289(0x273)](),_0x3dd1bb=_0x5640a1[_0x4b8289(0x273)]();if(_0x317d0c===_0x3dd1bb)return 0x1;if(_0x3dd1bb[_0x4b8289(0x20e)](_0x317d0c)||_0x317d0c[_0x4b8289(0x20e)](_0x3dd1bb))return 0.8;const _0x16cb4e=_0x317d0c[_0x4b8289(0x276)](/\s+/),_0x79789c=_0x3dd1bb['split'](/\s+/);let _0x1cf7d0=0x0;for(const _0x3450ca of _0x16cb4e){_0x3450ca[_0x4b8289(0x1c9)]>0x2&&_0x79789c[_0x4b8289(0x1e0)](_0x4944fb=>_0x4944fb[_0x4b8289(0x20e)](_0x3450ca)||_0x3450ca[_0x4b8289(0x20e)](_0x4944fb))&&_0x1cf7d0++;}return _0x1cf7d0/Math['max'](_0x16cb4e['length'],_0x79789c[_0x4b8289(0x1c9)]);}),_0x5df328=Math[_0x305427(0x1ce)](..._0x9d106d),_0x2d99e3=_0x9d106d[_0x305427(0x1fa)](_0x5df328);return{'bestMatch':{'target':_0x3fc62a[_0x2d99e3],'rating':_0x5df328},'bestMatchIndex':_0x2d99e3};}function searchMoviesMod(_0x4aefd8){return __async(this,null,function*(){const _0x55ddd3=_0x16d2;try{const _0x476d7b=yield getMoviesModDomain(),_0x281be4=_0x476d7b+_0x55ddd3(0x260)+encodeURIComponent(_0x4aefd8);console[_0x55ddd3(0x251)](_0x55ddd3(0x288)+_0x281be4);const _0x3e9ef6=yield makeRequest(_0x281be4),_0xad188b=yield _0x3e9ef6[_0x55ddd3(0x228)](),_0x2bbe0a=cheerio['load'](_0xad188b),_0x55d28d=[];return _0x2bbe0a(_0x55ddd3(0x1c6))[_0x55ddd3(0x209)]((_0x939e23,_0x4b2e6f)=>{const _0x33080b=_0x55ddd3,_0x599162=_0x2bbe0a(_0x4b2e6f)[_0x33080b(0x1c8)]('a'),_0x5dccb0=_0x599162[_0x33080b(0x256)]('title'),_0x59364a=_0x599162[_0x33080b(0x256)](_0x33080b(0x21b));_0x5dccb0&&_0x59364a&&_0x55d28d[_0x33080b(0x1de)]({'title':_0x5dccb0,'url':_0x59364a});}),console[_0x55ddd3(0x251)](_0x55ddd3(0x222)+_0x55d28d[_0x55ddd3(0x1c9)]+_0x55ddd3(0x1e7)),_0x55d28d;}catch(_0x529273){return console[_0x55ddd3(0x25b)](_0x55ddd3(0x1d5)+_0x529273[_0x55ddd3(0x215)]),[];}});}function extractDownloadLinks(_0x3161ce){return __async(this,null,function*(){const _0x216e4d=_0x16d2;try{const _0x316bee=yield makeRequest(_0x3161ce),_0x1b7697=yield _0x316bee['text'](),_0x30351c=cheerio[_0x216e4d(0x27e)](_0x1b7697),_0x347486=[],_0x1ab8f2=_0x30351c(_0x216e4d(0x23f)),_0x3e77a6=_0x1ab8f2['find'](_0x216e4d(0x292));return _0x3e77a6[_0x216e4d(0x209)]((_0x36eecf,_0x3c9c3d)=>{const _0xbb4d1=_0x216e4d,_0x6a9695=_0x30351c(_0x3c9c3d),_0x29eda4=_0x6a9695['text']()[_0xbb4d1(0x279)](),_0x2562a6=_0x6a9695[_0xbb4d1(0x27a)](_0xbb4d1(0x274));if(_0x6a9695['is']('h3')&&_0x29eda4['toLowerCase']()[_0xbb4d1(0x20e)](_0xbb4d1(0x239))){const _0x4be0de=_0x2562a6[_0xbb4d1(0x1c8)]('a')[_0xbb4d1(0x21a)]((_0x336664,_0x26ce81)=>{const _0x916ff3=_0xbb4d1,_0x1cffe6=_0x30351c(_0x26ce81)[_0x916ff3(0x228)]()[_0x916ff3(0x279)]()['toLowerCase']();return _0x1cffe6[_0x916ff3(0x20e)](_0x916ff3(0x1d3))&&!_0x1cffe6[_0x916ff3(0x20e)](_0x916ff3(0x1be));});_0x4be0de[_0xbb4d1(0x209)]((_0x41ef26,_0x82c418)=>{const _0x447184=_0xbb4d1,_0x36b036=_0x30351c(_0x82c418)['text']()[_0x447184(0x279)](),_0x14f0b7=_0x30351c(_0x82c418)['attr'](_0x447184(0x21b));_0x14f0b7&&_0x347486['push']({'quality':_0x29eda4+_0x447184(0x230)+_0x36b036,'url':_0x14f0b7});});}else{if(_0x6a9695['is']('h4')){const _0x14f2aa=_0x2562a6[_0xbb4d1(0x1c8)]('a.maxbutton-download-links,\x20.maxbutton')[_0xbb4d1(0x23d)]();if(_0x14f2aa[_0xbb4d1(0x1c9)]>0x0){const _0x7f9091=_0x14f2aa['attr'](_0xbb4d1(0x21b)),_0x100049=extractQuality(_0x29eda4);_0x7f9091&&_0x100049&&_0x347486[_0xbb4d1(0x1de)]({'quality':_0x100049,'url':_0x7f9091});}}}}),console[_0x216e4d(0x251)]('[MoviesMod]\x20Extracted\x20'+_0x347486[_0x216e4d(0x1c9)]+'\x20download\x20links'),_0x347486;}catch(_0x59c31b){return console[_0x216e4d(0x25b)](_0x216e4d(0x1fb)+_0x59c31b['message']),[];}});}function resolveIntermediateLink(_0x1876f4,_0xb06b9d,_0x2ae880){return __async(this,null,function*(){const _0x152235=_0x16d2;try{const _0x271dbd=new URL(_0x1876f4);if(_0x271dbd[_0x152235(0x1f5)]['includes'](_0x152235(0x213))||_0x271dbd['hostname'][_0x152235(0x20e)](_0x152235(0x289))){const _0x258dff=yield makeRequest(_0x1876f4,{'headers':{'Referer':_0xb06b9d}}),_0x30669a=yield _0x258dff[_0x152235(0x228)](),_0x543e14=cheerio[_0x152235(0x27e)](_0x30669a),_0x18e7b1=[];return _0x543e14(_0x152235(0x27d))[_0x152235(0x209)]((_0x333f55,_0x4cb14c)=>{const _0x202c28=_0x152235,_0x145f80=_0x543e14(_0x4cb14c)['attr']('href'),_0x23d0a1=_0x543e14(_0x4cb14c)['text']()[_0x202c28(0x279)]();_0x145f80&&_0x23d0a1&&!_0x23d0a1['toLowerCase']()['includes'](_0x202c28(0x1be))&&_0x18e7b1[_0x202c28(0x1de)]({'server':_0x23d0a1[_0x202c28(0x25d)](/\s+/g,'\x20'),'url':_0x145f80});}),_0x18e7b1[_0x152235(0x1c9)]===0x0&&_0x543e14(_0x152235(0x241))[_0x152235(0x209)]((_0x27909a,_0x564941)=>{const _0x289fc6=_0x152235,_0x17cd41=_0x543e14(_0x564941)[_0x289fc6(0x256)](_0x289fc6(0x21b)),_0xea5f99=_0x543e14(_0x564941)[_0x289fc6(0x228)]()['trim']();_0x17cd41&&_0xea5f99&&!_0xea5f99[_0x289fc6(0x273)]()[_0x289fc6(0x20e)](_0x289fc6(0x1be))&&_0x18e7b1['push']({'server':_0xea5f99[_0x289fc6(0x25d)](/\s+/g,'\x20')||_0x289fc6(0x24a),'url':_0x17cd41});}),console['log']('[MoviesMod]\x20Found\x20'+_0x18e7b1[_0x152235(0x1c9)]+_0x152235(0x22a)+_0x271dbd[_0x152235(0x1f5)]),_0x18e7b1;}else{if(_0x271dbd[_0x152235(0x1f5)][_0x152235(0x20e)](_0x152235(0x1fc))){const _0x4ae34f=yield makeRequest(_0x1876f4,{'headers':{'Referer':_0xb06b9d}}),_0x424a3a=yield _0x4ae34f[_0x152235(0x228)](),_0x2c0868=cheerio['load'](_0x424a3a),_0x28d1b6=[];return _0x2c0868('h3')[_0x152235(0x209)]((_0x85892c,_0x3e54b5)=>{const _0x399c6f=_0x152235,_0x2a9800=_0x2c0868(_0x3e54b5)[_0x399c6f(0x228)]()[_0x399c6f(0x279)](),_0x439098=_0x2a9800[_0x399c6f(0x29f)](/Episode\s+(\d+)/i);if(_0x439098){const _0x5eda9f=_0x439098[0x1],_0x1f5430=_0x2c0868(_0x3e54b5)[_0x399c6f(0x1c8)]('a')[_0x399c6f(0x23d)]();if(_0x1f5430[_0x399c6f(0x1c9)]>0x0){const _0x4076b5=_0x1f5430[_0x399c6f(0x256)](_0x399c6f(0x21b));_0x4076b5&&_0x28d1b6[_0x399c6f(0x1de)]({'server':_0x399c6f(0x1ea)+_0x5eda9f,'url':_0x4076b5});}}}),console[_0x152235(0x251)](_0x152235(0x222)+_0x28d1b6[_0x152235(0x1c9)]+'\x20episode\x20links\x20from\x20episodes.modpro.blog'),_0x28d1b6;}else{if(_0x271dbd['hostname']['includes']('modrefer.in')){const _0x13e911=_0x271dbd[_0x152235(0x275)]['get']('url');if(!_0x13e911)return console[_0x152235(0x25b)](_0x152235(0x225)),[];const _0x5dfe5f=atob(_0x13e911);console[_0x152235(0x251)]('[MoviesMod]\x20Decoded\x20modrefer\x20URL:\x20'+_0x5dfe5f);const _0x46a516=yield makeRequest(_0x5dfe5f,{'headers':{'User-Agent':_0x152235(0x229),'Referer':_0xb06b9d}}),_0x3b5245=yield _0x46a516[_0x152235(0x228)](),_0x43377d=cheerio[_0x152235(0x27e)](_0x3b5245),_0x14890c=[];return console[_0x152235(0x251)]('[MoviesMod]\x20Page\x20title:\x20'+_0x43377d(_0x152235(0x283))[_0x152235(0x228)]()),console[_0x152235(0x251)]('[MoviesMod]\x20Total\x20links\x20on\x20page:\x20'+_0x43377d('a')[_0x152235(0x1c9)]),console[_0x152235(0x251)](_0x152235(0x25e)+_0x3b5245['length']+'\x20characters'),_0x43377d(_0x152235(0x21c))[_0x152235(0x209)]((_0x438949,_0xe5a784)=>{const _0x51c8b5=_0x152235,_0x3008ad=_0x43377d(_0xe5a784)['attr'](_0x51c8b5(0x21b)),_0x3b36e5=_0x43377d(_0xe5a784)[_0x51c8b5(0x228)]()[_0x51c8b5(0x279)]();_0x3008ad&&_0x14890c[_0x51c8b5(0x1de)]({'server':_0x3b36e5,'url':_0x3008ad});}),_0x14890c[_0x152235(0x1c9)]===0x0&&(console[_0x152235(0x251)](_0x152235(0x278)),_0x43377d('a')[_0x152235(0x209)]((_0x199908,_0x4694fb)=>{const _0x220fce=_0x152235,_0x109e15=_0x43377d(_0x4694fb)[_0x220fce(0x256)](_0x220fce(0x21b)),_0x2c7e54=_0x43377d(_0x4694fb)[_0x220fce(0x228)]()[_0x220fce(0x279)]();_0x109e15&&(_0x109e15[_0x220fce(0x20e)](_0x220fce(0x1c1))||_0x109e15[_0x220fce(0x20e)](_0x220fce(0x23a))||_0x109e15['includes'](_0x220fce(0x28f))||_0x109e15[_0x220fce(0x20e)]('tech.creativeexpressionsblog.com')||_0x109e15[_0x220fce(0x20e)]('tech.examdegree.site'))&&(console[_0x220fce(0x251)](_0x220fce(0x243)+_0x2c7e54+_0x220fce(0x204)+_0x109e15),_0x14890c[_0x220fce(0x1de)]({'server':_0x2c7e54||'Download\x20Link','url':_0x109e15}));})),_0x14890c['length']===0x0&&(console[_0x152235(0x251)]('[MoviesMod]\x20Looking\x20for\x20alternative\x20download\x20patterns...'),_0x43377d(_0x152235(0x1ef))[_0x152235(0x209)]((_0x2188e5,_0x14616f)=>{const _0x1e0300=_0x152235,_0x172630=_0x43377d(_0x14616f),_0x95e141=_0x172630['attr'](_0x1e0300(0x21b))||_0x172630[_0x1e0300(0x256)]('data-href')||_0x172630[_0x1e0300(0x1c8)]('a')[_0x1e0300(0x256)](_0x1e0300(0x21b)),_0x3c52ed=_0x172630['text']()[_0x1e0300(0x279)]();_0x95e141&&(_0x95e141[_0x1e0300(0x20e)](_0x1e0300(0x1c1))||_0x95e141['includes']('cloud.unblockedgames.world')||_0x95e141[_0x1e0300(0x20e)](_0x1e0300(0x28f))||_0x95e141[_0x1e0300(0x20e)](_0x1e0300(0x26b))||_0x95e141[_0x1e0300(0x20e)](_0x1e0300(0x24f)))&&(console[_0x1e0300(0x251)]('[MoviesMod]\x20Found\x20alternative\x20link:\x20'+_0x3c52ed+'\x20->\x20'+_0x95e141),_0x14890c[_0x1e0300(0x1de)]({'server':_0x3c52ed||_0x1e0300(0x247),'url':_0x95e141}));})),console['log'](_0x152235(0x222)+_0x14890c['length']+_0x152235(0x20f)),_0x14890c;}}}return[];}catch(_0x470b90){return console[_0x152235(0x25b)](_0x152235(0x202)+_0x470b90['message']),[];}});}function resolveTechUnblockedLink(_0x3fffe2){return __async(this,null,function*(){const _0x157e64=_0x16d2;console[_0x157e64(0x251)](_0x157e64(0x27c)+_0x3fffe2);try{const _0xccc899=yield makeRequest(_0x3fffe2),_0x3d26e8=yield _0xccc899[_0x157e64(0x228)](),_0x480042=cheerio[_0x157e64(0x27e)](_0x3d26e8),_0x1311fb=_0x480042(_0x157e64(0x250)),_0xa8ddb8=_0x1311fb['find'](_0x157e64(0x20a))[_0x157e64(0x27f)](),_0x5b33a4=_0x1311fb[_0x157e64(0x256)](_0x157e64(0x1d8));if(!_0xa8ddb8||!_0x5b33a4)return console['error']('\x20\x20[SID]\x20Error:\x20Could\x20not\x20find\x20_wp_http\x20in\x20initial\x20form.'),null;const _0x4159eb=new URLSearchParams({'_wp_http':_0xa8ddb8}),_0x531788=yield makeRequest(_0x5b33a4,{'method':_0x157e64(0x299),'headers':{'Referer':_0x3fffe2,'Content-Type':'application/x-www-form-urlencoded'},'body':_0x4159eb[_0x157e64(0x1cb)]()}),_0x5311e2=yield _0x531788['text'](),_0x49ba39=cheerio[_0x157e64(0x27e)](_0x5311e2),_0x4a6b3a=_0x49ba39(_0x157e64(0x250)),_0x5b2c21=_0x4a6b3a[_0x157e64(0x256)]('action'),_0xbb8acf=_0x4a6b3a[_0x157e64(0x1c8)](_0x157e64(0x244))[_0x157e64(0x27f)](),_0x2df42e=_0x4a6b3a[_0x157e64(0x1c8)](_0x157e64(0x277))[_0x157e64(0x27f)]();if(!_0x5b2c21)return console[_0x157e64(0x25b)](_0x157e64(0x257)),null;const _0x4952a2=new URLSearchParams({'_wp_http2':_0xbb8acf,'token':_0x2df42e}),_0x109871=yield makeRequest(_0x5b2c21,{'method':_0x157e64(0x299),'headers':{'Referer':_0x531788['url'],'Content-Type':_0x157e64(0x1eb)},'body':_0x4952a2[_0x157e64(0x1cb)]()}),_0x27678a=yield _0x109871['text']();let _0x13a4de=null,_0x396297=null,_0x14c93d=null;const _0x497fc9=_0x27678a[_0x157e64(0x29f)](/s_343\('([^']+)',\s*'([^']+)'/),_0x1ef252=_0x27678a[_0x157e64(0x29f)](/c\.setAttribute\("href",\s*"([^"]+)"\)/);_0x497fc9&&(_0x396297=_0x497fc9[0x1]['trim'](),_0x14c93d=_0x497fc9[0x2][_0x157e64(0x279)]());_0x1ef252&&(_0x13a4de=_0x1ef252[0x1][_0x157e64(0x279)]());if(!_0x13a4de||!_0x396297||!_0x14c93d)return console[_0x157e64(0x25b)]('\x20\x20[SID]\x20Error:\x20Could\x20not\x20extract\x20dynamic\x20cookie/link\x20from\x20JS.'),null;const {origin:_0x1403e9}=new URL(_0x3fffe2),_0x15191b=new URL(_0x13a4de,_0x1403e9)[_0x157e64(0x21b)],_0x2d2d8c=yield makeRequest(_0x15191b,{'headers':{'Referer':_0x109871[_0x157e64(0x1f0)],'Cookie':_0x396297+'='+_0x14c93d}}),_0x7268fc=yield _0x2d2d8c[_0x157e64(0x228)](),_0xb395b3=cheerio[_0x157e64(0x27e)](_0x7268fc),_0x17a228=_0xb395b3(_0x157e64(0x29c));if(_0x17a228[_0x157e64(0x1c9)]>0x0){const _0xa160a8=_0x17a228['attr'](_0x157e64(0x1bf)),_0x1ed60c=_0xa160a8[_0x157e64(0x29f)](/url=(.*)/i);if(_0x1ed60c&&_0x1ed60c[0x1]){const _0x270ca9=_0x1ed60c[0x1]['replace'](/"/g,'')['replace'](/'/g,'');return console['log']('\x20\x20[SID]\x20SUCCESS!\x20Resolved\x20Driveleech\x20URL:\x20'+_0x270ca9),_0x270ca9;}}return console[_0x157e64(0x25b)](_0x157e64(0x254)),null;}catch(_0x5dc1dd){return console[_0x157e64(0x25b)](_0x157e64(0x1ba)+_0x5dc1dd[_0x157e64(0x215)]),null;}});}function resolveDriveseedLink(_0x1dbcfd){return __async(this,null,function*(){const _0x45a9df=_0x16d2;try{const _0x107aa8=yield makeRequest(_0x1dbcfd,{'headers':{'Referer':'https://links.modpro.blog/'}}),_0x74ddc9=yield _0x107aa8[_0x45a9df(0x228)](),_0x3b16eb=_0x74ddc9[_0x45a9df(0x29f)](/window\.location\.replace\("([^"]+)"\)/);if(_0x3b16eb&&_0x3b16eb[0x1]){const _0x92907a=_0x3b16eb[0x1],_0x56de78=_0x45a9df(0x263)+_0x92907a,_0x79f7bd=yield makeRequest(_0x56de78,{'headers':{'Referer':_0x1dbcfd}}),_0x393980=yield _0x79f7bd['text'](),_0x9e20c5=cheerio[_0x45a9df(0x27e)](_0x393980),_0x32d1e=[];let _0x27d291=null,_0x4ebf0c=null;_0x9e20c5('ul.list-group\x20li')[_0x45a9df(0x209)]((_0x1617b9,_0x1cb3a5)=>{const _0x2177f8=_0x45a9df,_0x494cf4=_0x9e20c5(_0x1cb3a5)[_0x2177f8(0x228)]();if(_0x494cf4[_0x2177f8(0x20e)](_0x2177f8(0x218)))_0x27d291=_0x494cf4[_0x2177f8(0x276)](':')[0x1][_0x2177f8(0x279)]();else _0x494cf4[_0x2177f8(0x20e)]('Name\x20:')&&(_0x4ebf0c=_0x494cf4[_0x2177f8(0x276)](':')[0x1]['trim']());});const _0x13544f=_0x9e20c5(_0x45a9df(0x205))['attr'](_0x45a9df(0x21b));_0x13544f&&_0x32d1e['push']({'title':_0x45a9df(0x238),'type':_0x45a9df(0x265),'url':_0x45a9df(0x263)+_0x13544f,'priority':0x1});const _0x79edc9=_0x9e20c5('a:contains(\x22Resume\x20Worker\x20Bot\x22)')[_0x45a9df(0x256)](_0x45a9df(0x21b));_0x79edc9&&_0x32d1e['push']({'title':_0x45a9df(0x1f4),'type':_0x45a9df(0x248),'url':_0x79edc9,'priority':0x2});_0x9e20c5(_0x45a9df(0x1f6))[_0x45a9df(0x209)]((_0xe00815,_0x10ad7f)=>{const _0x1870da=_0x45a9df,_0x35ec0e=_0x9e20c5(_0x10ad7f)['attr'](_0x1870da(0x21b)),_0x19d15b=_0x9e20c5(_0x10ad7f)[_0x1870da(0x228)]()[_0x1870da(0x279)]();_0x35ec0e&&_0x19d15b&&!_0x32d1e['some'](_0x374564=>_0x374564[_0x1870da(0x1f0)]===_0x35ec0e)&&_0x32d1e[_0x1870da(0x1de)]({'title':_0x19d15b,'type':_0x1870da(0x269),'url':_0x35ec0e[_0x1870da(0x1fd)](_0x1870da(0x1e5))?_0x35ec0e:'https://driveseed.org'+_0x35ec0e,'priority':0x4});});const _0x4bbf1b=_0x9e20c5('a:contains(\x22Instant\x20Download\x22)')['attr']('href');return _0x4bbf1b&&_0x32d1e[_0x45a9df(0x1de)]({'title':_0x45a9df(0x203),'type':_0x45a9df(0x1f7),'url':_0x4bbf1b,'priority':0x3}),_0x32d1e[_0x45a9df(0x26f)]((_0x44ad5e,_0x2f8a57)=>_0x44ad5e[_0x45a9df(0x20b)]-_0x2f8a57[_0x45a9df(0x20b)]),{'downloadOptions':_0x32d1e,'size':_0x27d291,'fileName':_0x4ebf0c};}return{'downloadOptions':[],'size':null,'fileName':null};}catch(_0x1e9bb1){return console[_0x45a9df(0x25b)](_0x45a9df(0x20d)+_0x1e9bb1[_0x45a9df(0x215)]),{'downloadOptions':[],'size':null,'fileName':null};}});}function resolveResumeCloudLink(_0x461df4){return __async(this,null,function*(){const _0x1ca7b3=_0x16d2;try{const _0x1e0966=yield makeRequest(_0x461df4,{'headers':{'Referer':'https://driveseed.org/'}}),_0x55063f=yield _0x1e0966[_0x1ca7b3(0x228)](),_0x5d7bb4=cheerio['load'](_0x55063f),_0xa1c2cb=_0x5d7bb4(_0x1ca7b3(0x223))['attr'](_0x1ca7b3(0x21b));return _0xa1c2cb||null;}catch(_0x77caa0){return console['error'](_0x1ca7b3(0x211)+_0x77caa0[_0x1ca7b3(0x215)]),null;}});}function resolveVideoSeedLink(_0xac1630){return __async(this,null,function*(){const _0x376952=_0x16d2;try{const _0x393202=new URLSearchParams(new URL(_0xac1630)[_0x376952(0x29e)]),_0x1fe575=_0x393202[_0x376952(0x286)]('url');if(_0x1fe575){const _0x4794c7=new URL(_0xac1630)[_0x376952(0x249)]+_0x376952(0x272),_0x532db5=new URLSearchParams();_0x532db5['append'](_0x376952(0x1c3),_0x1fe575);const _0x5c79df=yield fetch(_0x4794c7,{'method':_0x376952(0x299),'body':_0x532db5,'headers':{'Content-Type':'application/x-www-form-urlencoded','x-token':new URL(_0xac1630)['hostname'],'User-Agent':_0x376952(0x1e4)}});if(_0x5c79df['ok']){const _0x10cfc9=yield _0x5c79df[_0x376952(0x28a)]();if(_0x10cfc9&&_0x10cfc9['url'])return _0x10cfc9[_0x376952(0x1f0)];}}return null;}catch(_0x101725){return console[_0x376952(0x25b)](_0x376952(0x1df)+_0x101725[_0x376952(0x215)]),null;}});}function validateVideoUrl(_0x4fcbe4,_0x44073e=0x2710){return __async(this,null,function*(){const _0x4b0231=_0x16d2;try{console['log'](_0x4b0231(0x235)+_0x4fcbe4[_0x4b0231(0x227)](0x0,0x64)+_0x4b0231(0x1e2));const _0x48b029=yield fetch(_0x4fcbe4,{'method':'HEAD','headers':{'Range':_0x4b0231(0x224),'User-Agent':_0x4b0231(0x1e4)}});return _0x48b029['ok']||_0x48b029[_0x4b0231(0x220)]===0xce?(console['log']('[MoviesMod]\x20✓\x20URL\x20validation\x20successful\x20('+_0x48b029[_0x4b0231(0x220)]+')'),!![]):(console[_0x4b0231(0x251)](_0x4b0231(0x1e8)+_0x48b029[_0x4b0231(0x220)]),![]);}catch(_0x4b69bd){return console[_0x4b0231(0x251)]('[MoviesMod]\x20✗\x20URL\x20validation\x20failed:\x20'+_0x4b69bd[_0x4b0231(0x215)]),![];}});}function getStreams(_0x46670d,_0x50f2c9=_0x51a88a(0x281),_0x2dc05c=null,_0x55e666=null){return __async(this,null,function*(){const _0x413bee=_0x16d2;var _0x2a4aa3,_0x28bd8e;console[_0x413bee(0x251)]('[MoviesMod]\x20Fetching\x20streams\x20for\x20TMDB\x20ID:\x20'+_0x46670d+',\x20Type:\x20'+_0x50f2c9+(_0x2dc05c?',\x20S'+_0x2dc05c+'E'+_0x55e666:''));try{const _0xe91cf5=_0x413bee(0x290)+(_0x50f2c9==='tv'?'tv':'movie')+'/'+_0x46670d+_0x413bee(0x1d0)+TMDB_API_KEY+_0x413bee(0x25a),_0x298746=yield makeRequest(_0xe91cf5),_0x478408=yield _0x298746[_0x413bee(0x28a)](),_0x7b9d28=_0x50f2c9==='tv'?_0x478408[_0x413bee(0x295)]:_0x478408[_0x413bee(0x283)],_0x116d6a=_0x50f2c9==='tv'?(_0x2a4aa3=_0x478408['first_air_date'])==null?void 0x0:_0x2a4aa3['substring'](0x0,0x4):(_0x28bd8e=_0x478408[_0x413bee(0x1d4)])==null?void 0x0:_0x28bd8e['substring'](0x0,0x4),_0x3e5215=_0x478408[_0x413bee(0x26c)]?_0x478408['external_ids'][_0x413bee(0x267)]:null;if(!_0x7b9d28)throw new Error(_0x413bee(0x285));console[_0x413bee(0x251)](_0x413bee(0x253)+_0x7b9d28+_0x413bee(0x246)+_0x116d6a+_0x413bee(0x1dd)+(_0x3e5215||_0x413bee(0x210))+']');let _0x11da42=[],_0x27840b=null;if(_0x3e5215){const _0xd6f836=_0x50f2c9==='tv'&&_0x2dc05c?_0x3e5215+'\x20Season\x20'+_0x2dc05c:_0x3e5215;console[_0x413bee(0x251)](_0x413bee(0x1ec)+_0xd6f836),_0x11da42=yield searchMoviesMod(_0xd6f836),_0x11da42[_0x413bee(0x1c9)]>0x0&&(console[_0x413bee(0x251)](_0x413bee(0x1e1)+_0x11da42[0x0]['title']),_0x27840b=_0x11da42[0x0]);}if(!_0x27840b){console[_0x413bee(0x251)](_0x413bee(0x221)+_0x7b9d28);const _0x9eb56c=_0x50f2c9==='tv'&&_0x2dc05c?_0x7b9d28+'\x20Season\x20'+_0x2dc05c:_0x7b9d28;_0x11da42=yield searchMoviesMod(_0x9eb56c);_0x11da42[_0x413bee(0x1c9)]===0x0&&(_0x11da42=yield searchMoviesMod(_0x7b9d28));if(_0x11da42[_0x413bee(0x1c9)]===0x0)return console['log'](_0x413bee(0x1d7)),[];const _0x4bd090=_0x11da42[_0x413bee(0x200)](_0x3009c5=>_0x3009c5['title']),_0x10ae8c=findBestMatch(_0x7b9d28,_0x4bd090);console[_0x413bee(0x251)](_0x413bee(0x236)+_0x7b9d28+_0x413bee(0x22f)+_0x10ae8c[_0x413bee(0x1ff)]['target']+_0x413bee(0x24e)+_0x10ae8c[_0x413bee(0x1ff)][_0x413bee(0x22e)][_0x413bee(0x1c2)](0x2));_0x10ae8c[_0x413bee(0x1ff)][_0x413bee(0x22e)]>0.3&&(_0x27840b=_0x11da42[_0x10ae8c[_0x413bee(0x1d2)]],_0x50f2c9===_0x413bee(0x281)&&_0x116d6a&&(!_0x27840b[_0x413bee(0x283)][_0x413bee(0x20e)](_0x116d6a)&&(console['warn'](_0x413bee(0x21f)+_0x27840b['title']+_0x413bee(0x240)+_0x116d6a+_0x413bee(0x1bd)),_0x27840b=null)));if(!_0x27840b){console[_0x413bee(0x251)]('[MoviesMod]\x20Similarity\x20match\x20failed.\x20Trying\x20stricter\x20search...');const _0x267999=new RegExp('\x5cb'+escapeRegExp(_0x7b9d28[_0x413bee(0x273)]())+'\x5cb');_0x50f2c9===_0x413bee(0x281)?_0x27840b=_0x11da42['find'](_0x510749=>_0x267999[_0x413bee(0x24b)](_0x510749['title'][_0x413bee(0x273)]())&&(!_0x116d6a||_0x510749['title'][_0x413bee(0x20e)](_0x116d6a))):_0x27840b=_0x11da42[_0x413bee(0x1c8)](_0x403275=>_0x267999['test'](_0x403275[_0x413bee(0x283)][_0x413bee(0x273)]())&&_0x403275[_0x413bee(0x283)][_0x413bee(0x273)]()['includes']('season'));}}if(!_0x27840b)return console[_0x413bee(0x251)](_0x413bee(0x1ee)+_0x7b9d28+'\x20('+_0x116d6a+')\x22'),[];console[_0x413bee(0x251)](_0x413bee(0x28d)+_0x27840b[_0x413bee(0x283)]);const _0xf68617=yield extractDownloadLinks(_0x27840b[_0x413bee(0x1f0)]);if(_0xf68617[_0x413bee(0x1c9)]===0x0)return console[_0x413bee(0x251)](_0x413bee(0x23c)),[];let _0x476abf=_0xf68617;(_0x50f2c9==='tv'||_0x50f2c9===_0x413bee(0x266))&&_0x2dc05c!==null&&(_0x476abf=_0xf68617[_0x413bee(0x21a)](_0x8112e2=>_0x8112e2[_0x413bee(0x214)][_0x413bee(0x273)]()['includes'](_0x413bee(0x282)+_0x2dc05c)||_0x8112e2[_0x413bee(0x214)][_0x413bee(0x273)]()[_0x413bee(0x20e)]('s'+_0x2dc05c)));_0x476abf=_0x476abf[_0x413bee(0x21a)](_0x1bacf1=>!_0x1bacf1[_0x413bee(0x214)][_0x413bee(0x273)]()[_0x413bee(0x20e)](_0x413bee(0x1ed))),console['log'](_0x413bee(0x237)+_0x476abf[_0x413bee(0x1c9)]+'\x20links\x20remaining\x20after\x20480p\x20filter.');if(_0x476abf[_0x413bee(0x1c9)]===0x0)return console[_0x413bee(0x251)](_0x413bee(0x258)),[];const _0x2304fe=_0x476abf[_0x413bee(0x200)](_0x355dad=>__async(this,null,function*(){const _0x2b842c=_0x413bee;var _0x47c90b;try{const _0x3a25d4=yield resolveIntermediateLink(_0x355dad['url'],_0x27840b[_0x2b842c(0x1f0)],_0x355dad[_0x2b842c(0x214)]);if(!_0x3a25d4||_0x3a25d4[_0x2b842c(0x1c9)]===0x0)return console[_0x2b842c(0x251)](_0x2b842c(0x261)+_0x355dad[_0x2b842c(0x214)]),null;const _0x347658=[];for(const _0x1e1ed8 of _0x3a25d4){let _0x31d4d4=_0x1e1ed8[_0x2b842c(0x1f0)];const _0x27d988=_0x1e1ed8['server']&&_0x1e1ed8[_0x2b842c(0x234)]['toLowerCase']()[_0x2b842c(0x20e)]('episode');console['log'](_0x2b842c(0x28c)+_0x1e1ed8[_0x2b842c(0x234)]+'\x22,\x20isEpisodeLink='+_0x27d988+_0x2b842c(0x233)+_0x1e1ed8[_0x2b842c(0x1f0)][_0x2b842c(0x227)](0x0,0x32)+'...');if(_0x31d4d4[_0x2b842c(0x20e)]('cloud.unblockedgames.world')||_0x31d4d4['includes'](_0x2b842c(0x26b))||_0x31d4d4[_0x2b842c(0x20e)](_0x2b842c(0x28f))){const _0x575f9f=yield resolveTechUnblockedLink(_0x31d4d4);if(!_0x575f9f)continue;_0x31d4d4=_0x575f9f;}if(_0x31d4d4&&_0x31d4d4[_0x2b842c(0x20e)]('driveseed.org')){console['log'](_0x2b842c(0x296)+_0x31d4d4[_0x2b842c(0x227)](0x0,0x50)+_0x2b842c(0x1e2));const _0x1d8929=yield resolveDriveseedLink(_0x31d4d4);console[_0x2b842c(0x251)](_0x2b842c(0x297)+(_0x1d8929?_0x2b842c(0x287)+(((_0x47c90b=_0x1d8929[_0x2b842c(0x291)])==null?void 0x0:_0x47c90b[_0x2b842c(0x1c9)])||0x0):_0x2b842c(0x1f8)));if(_0x1d8929&&_0x1d8929[_0x2b842c(0x291)]&&_0x1d8929[_0x2b842c(0x291)][_0x2b842c(0x1c9)]>0x0){console[_0x2b842c(0x251)](_0x2b842c(0x29b)+_0x1d8929[_0x2b842c(0x291)][_0x2b842c(0x200)](_0x40fd1d=>_0x40fd1d[_0x2b842c(0x1cd)]+':\x20'+_0x40fd1d[_0x2b842c(0x283)])['join'](',\x20'));const _0x2619e1=_0x1d8929[_0x2b842c(0x291)][_0x2b842c(0x26f)]((_0x4290e4,_0xbcd802)=>_0x4290e4[_0x2b842c(0x20b)]-_0xbcd802[_0x2b842c(0x20b)]);let _0x352806=null,_0x4b985f=null;for(const _0x525bb1 of _0x2619e1){console[_0x2b842c(0x251)]('[MoviesMod]\x20Trying\x20'+_0x525bb1['title']+'\x20('+_0x525bb1['type']+_0x2b842c(0x1da)+_0x355dad[_0x2b842c(0x214)]+_0x2b842c(0x1e2));if(_0x525bb1[_0x2b842c(0x1cd)]===_0x2b842c(0x265)||_0x525bb1[_0x2b842c(0x1cd)]===_0x2b842c(0x248))_0x352806=yield resolveResumeCloudLink(_0x525bb1[_0x2b842c(0x1f0)]),console[_0x2b842c(0x251)]('[MoviesMod]\x20Resume/Worker\x20result:\x20'+(_0x352806?'got\x20URL':_0x2b842c(0x1f8)));else{if(_0x525bb1['type']==='instant')_0x352806=yield resolveVideoSeedLink(_0x525bb1[_0x2b842c(0x1f0)]),console[_0x2b842c(0x251)](_0x2b842c(0x1d6)+(_0x352806?_0x2b842c(0x1c5):_0x2b842c(0x1f8))),!_0x352806&&(_0x352806=_0x525bb1[_0x2b842c(0x1f0)],console['log'](_0x2b842c(0x1dc)));else _0x525bb1['type']===_0x2b842c(0x269)&&(_0x352806=_0x525bb1['url'],console[_0x2b842c(0x251)]('[MoviesMod]\x20Generic\x20result:\x20using\x20URL\x20directly'));}if(_0x352806){const _0x46fb9d=yield validateVideoUrl(_0x352806);if(_0x46fb9d){_0x4b985f=_0x525bb1[_0x2b842c(0x283)],console[_0x2b842c(0x251)](_0x2b842c(0x1f1)+_0x4b985f);break;}else console[_0x2b842c(0x251)]('[MoviesMod]\x20✗\x20'+_0x525bb1['title']+_0x2b842c(0x1e9)),_0x352806=null;}}if(_0x352806){console[_0x2b842c(0x251)](_0x2b842c(0x270));if(_0x27d988&&_0x55e666!==null){const _0xe71670=_0x1e1ed8['server']['match'](/Episode\s+(\d+)/i);console['log']('[MoviesMod]\x20Episode\x20filtering:\x20server=\x22'+_0x1e1ed8[_0x2b842c(0x234)]+_0x2b842c(0x293)+_0x55e666+_0x2b842c(0x1cc)+(_0xe71670?_0xe71670[0x1]:'none'));if(_0xe71670&&parseInt(_0xe71670[0x1])!==_0x55e666){console[_0x2b842c(0x251)](_0x2b842c(0x22c)+_0xe71670[0x1]+_0x2b842c(0x298)+_0x55e666+')');continue;}else _0xe71670&&parseInt(_0xe71670[0x1])===_0x55e666&&console[_0x2b842c(0x251)](_0x2b842c(0x1f2)+_0x55e666+_0x2b842c(0x20c));}const _0x310aeb=_0x50f2c9==='tv'&&_0x2dc05c&&_0x55e666?_0x27840b[_0x2b842c(0x283)]+'\x20S'+_0x2dc05c['toString']()[_0x2b842c(0x28e)](0x2,'0')+'E'+_0x55e666[_0x2b842c(0x1cb)]()[_0x2b842c(0x28e)](0x2,'0'):_0x27840b[_0x2b842c(0x283)];_0x347658[_0x2b842c(0x1de)]({'name':(_0x2b842c(0x1f9)+(_0x1e1ed8[_0x2b842c(0x234)]||'')+_0x2b842c(0x230)+_0x355dad[_0x2b842c(0x214)])[_0x2b842c(0x279)](),'title':_0x310aeb,'url':_0x352806,'quality':_0x355dad[_0x2b842c(0x214)],'size':_0x1d8929['size']||_0x2b842c(0x1ca),'headers':{'User-Agent':_0x2b842c(0x242),'Referer':_0x2b842c(0x27b)},'provider':'moviesmod'});break;}}}}const _0x367ad3=_0x347658[_0x2b842c(0x1c9)]>0x0?_0x347658[0x0]:null;return console[_0x2b842c(0x251)]('[MoviesMod]\x20Returning\x20'+(_0x367ad3?_0x2b842c(0x25f):_0x2b842c(0x1f8))+'\x20for\x20'+_0x355dad['quality']),_0x367ad3;}catch(_0x4fb5c0){return console[_0x2b842c(0x25b)](_0x2b842c(0x245)+_0x355dad[_0x2b842c(0x214)]+':\x20'+_0x4fb5c0['message']),null;}})),_0x2a5bd2=yield Promise['all'](_0x2304fe);console['log'](_0x413bee(0x219)+_0x2a5bd2[_0x413bee(0x1c9)]),_0x2a5bd2[_0x413bee(0x1bb)]((_0x2e100d,_0x4d84b1)=>{const _0x9c8bee=_0x413bee;console[_0x9c8bee(0x251)](_0x9c8bee(0x23e)+_0x4d84b1+']\x20'+(_0x2e100d?_0x9c8bee(0x217):'NULL'));});const _0x54ede1=_0x2a5bd2[_0x413bee(0x21a)](Boolean);return console[_0x413bee(0x251)](_0x413bee(0x21d)+_0x54ede1[_0x413bee(0x1c9)]),_0x54ede1[_0x413bee(0x26f)]((_0x1ec887,_0x35e9fc)=>{const _0x372610=_0x413bee,_0x1ee84e=parseQualityForSort(_0x1ec887[_0x372610(0x214)]),_0x45daeb=parseQualityForSort(_0x35e9fc['quality']);return _0x45daeb-_0x1ee84e;}),console[_0x413bee(0x251)](_0x413bee(0x21e)+_0x54ede1[_0x413bee(0x1c9)]+_0x413bee(0x1fe)),_0x54ede1;}catch(_0x4da171){return console[_0x413bee(0x25b)](_0x413bee(0x1c7)+_0x4da171[_0x413bee(0x215)]),[];}});}typeof module!=='undefined'&&module[_0x51a88a(0x207)]?module[_0x51a88a(0x207)]={'getStreams':getStreams}:global[_0x51a88a(0x1d9)]=getStreams;






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
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:3bb5ac244c64 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://moviesmod.zone","providerName":"moviesmod","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"budgetMs":45000,"languageHint":"","implementationRevision":"native-media-filename-identity-v3"});

/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:a7e43845497d */
;(function(g,c){"use strict";
var ASSET=/\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|otf|eot|json|xml|vtt|srt)(?:[?#]|$)/i;
var BADHOST=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|googletagmanager\.com|google-analytics\.com|doubleclick\.net)$/i;
var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return""}}
function rejected(v){var h=host(v);return !/^https?:\/\//i.test(v)||!h||BADHOST.test(h)||ASSET.test(v)||/(?:trailer|bande-annonce|big[_-]?buck[_-]?bunny|sample[-_]?video|\/troll\/master\.m3u8)/i.test(v)}
function directByName(v){return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/hls2?\//i.test(v)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function keyOf(o,name){var keys=Object.keys(o||{}),want=String(name||"").toLowerCase();for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===want)return keys[i];return""}
function setHeader(o,name,value){if(!value)return;var k=keyOf(o,name);if(k&&k!==name)delete o[k];o[name]=String(value)}
function baseHeaders(row){
  var out={};
  function merge(src){if(src&&typeof src==="object")Object.keys(src).forEach(function(k){if(String(k).toLowerCase()!=="range"&&s(src[k]))out[k]=s(src[k])})}
  try{merge(row&&row.headers)}catch(_e){}
  try{merge(row&&row.requestHeaders)}catch(_e){}
  try{merge(row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request)}catch(_e){}
  return out;
}
function splitSetCookie(value){
  var raw=s(value);if(!raw)return[];
  return raw.split(/,(?=\s*[^;,=\s]+\s*=)/g).map(function(x){return x.trim()}).filter(Boolean);
}
function defaultPath(url){try{var p=new URL(url).pathname||"/";if(p.charAt(0)!=="/")return"/";var i=p.lastIndexOf("/");return i<=0?"/":p.slice(0,i+1)}catch(_e){return"/"}}
function rememberCookie(jar,setCookie,url){
  if(!jar||!setCookie)return;
  var parsed;try{parsed=new URL(url)}catch(_e){return}
  splitSetCookie(setCookie).forEach(function(line){
    var parts=line.split(";"),first=s(parts.shift()),eq=first.indexOf("=");if(eq<=0)return;
    var name=s(first.slice(0,eq)),value=s(first.slice(eq+1));if(!name)return;
    var item={name:name,value:value,domain:parsed.hostname.toLowerCase(),hostOnly:true,path:defaultPath(url),secure:false,expired:false};
    parts.forEach(function(part){var x=s(part),i=x.indexOf("="),ak=(i>=0?x.slice(0,i):x).trim().toLowerCase(),av=i>=0?s(x.slice(i+1)):"";
      if(ak==="domain"&&av){item.domain=av.replace(/^\./,"").toLowerCase();item.hostOnly=false}
      else if(ak==="path"&&av.charAt(0)==="/")item.path=av;
      else if(ak==="secure")item.secure=true;
      else if(ak==="max-age"&&Number(av)<=0)item.expired=true;
      else if(ak==="expires"){var ts=Date.parse(av);if(Number.isFinite(ts)&&ts<=Date.now())item.expired=true}
    });
    var id=item.name.toLowerCase()+"|"+item.domain+"|"+item.path;
    for(var i=jar.length-1;i>=0;i--){var old=jar[i],oldId=old.name.toLowerCase()+"|"+old.domain+"|"+old.path;if(oldId===id)jar.splice(i,1)}
    if(!item.expired&&item.value)jar.push(item);
  });
}
function captureCookies(jar,response,url){
  try{if(!response||!response.headers||typeof response.headers.get!=="function")return;var v=response.headers.get("set-cookie")||response.headers.get("Set-Cookie");if(v)rememberCookie(jar,v,url)}catch(_e){}
}
function cookieHeader(jar,target){
  var u;try{u=new URL(target)}catch(_e){return""}
  var h=u.hostname.toLowerCase(),p=u.pathname||"/",secure=u.protocol==="https:",out=[];
  (jar||[]).forEach(function(x){var domainOk=x.hostOnly?h===x.domain:(h===x.domain||h.endsWith("."+x.domain));if(!domainOk)return;if(x.secure&&!secure)return;if(p.indexOf(x.path)!==0)return;out.push(x.name+"="+x.value)});
  return out.join("; ");
}
function mergeCookies(a,b){
  var order=[],map={};function add(raw){s(raw).split(";").forEach(function(part){var x=s(part),i=x.indexOf("=");if(i<=0)return;var n=s(x.slice(0,i)),v=s(x.slice(i+1)),k=n.toLowerCase();if(!map[k])order.push(k);map[k]={n:n,v:v}})}add(a);add(b);return order.map(function(k){return map[k].n+"="+map[k].v}).join("; ")
}
function headers(row,referer,target,jar){
  var out=baseHeaders(row);
  if(referer){setHeader(out,"Referer",referer);try{setHeader(out,"Origin",new URL(referer).origin)}catch(_e){}}
  if(!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",DEFAULT_UA);
  var scoped=cookieHeader(jar,target),existing=keyOf(out,"Cookie");if(scoped)setHeader(out,"Cookie",mergeCookies(existing?out[existing]:"",scoped));
  if(!directByName(target)&&!keyOf(out,"Range"))out.Range="bytes=0-262143";
  return out;
}
function kindBytes(bytes){if(!bytes||bytes.length<4)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes[0]===71&&(bytes.length<189||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var x="";for(var i=0;i<Math.min(bytes.length,262144);i++)x+=String.fromCharCode(bytes[i]);return x}}
async function fetchResource(url,row,referer,jar){try{
  var requestHeaders=headers(row,referer,url,jar),r=await g.fetch(url,{headers:requestHeaders,redirect:"follow",signal:timeout()});if(!r)return null;
  captureCookies(jar,r,s(r.url||url));
  var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",bytes=null,text="";
  if(typeof r.arrayBuffer==="function"){var buf=await r.arrayBuffer();bytes=new Uint8Array(buf);text=decode(bytes.slice(0,300000))}
  else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}
  return{ok:!!r.ok,status:r.status,url:s(r.url||url),type:type,bytes:bytes,text:text,headers:headers(row,referer,r.url||url,jar)}
}catch(_){return null}}
function proof(r){if(!r||!r.ok)return null;var t=s(r.text).trimStart();if(t.indexOf("#EXTM3U")===0)return"hls";if(/<MPD[\s>]/i.test(t.slice(0,4096))||/application\/dash\+xml/i.test(r.type))return"dash";var b=kindBytes(r.bytes);if(b)return b;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;out.push(u)}var body=s(text),patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mpd|mp4|mkv|webm|embed|player|\/e\/|\/hls2?\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null){add(m[1]);if(out.length>=c.maxCandidates)return out}}return out}
async function resolve(url,row,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(url))return[];seen=seen||{};if(seen[url])return[];seen[url]=1;var r=await fetchResource(url,row,referer,jar);if(!r)return[];var k=proof(r);if(k)return[{url:r.url||url,kind:k,headers:r.headers}];if(!/html|text|json|javascript|xml/i.test(r.type)&&!/[<>{}\[\]"']/.test(r.text||""))return[];var next=candidates(r.text,r.url||url),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var found=await resolve(next[i],row,r.url||url,depth+1,seen,jar);for(var j=0;j<found.length;j++)if(!out.some(function(x){return x.url===found[j].url}))out.push(found[j])}return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function clone(row,media){var out=Object.assign({},row,{url:media.url,headers:media.headers||row.headers||{},isDirect:true,type:media.kind});if(media.kind==="hls"&&"format" in out)out.format="m3u8";if(media.kind==="dash"&&"format" in out)out.format="mpd";return out}
function refererOf(row,u){var h=baseHeaders(row),k=keyOf(h,"Referer");return s(k?h[k]:(row&&(row.referer||row.referrer||row.playerUrl||row.embedUrl||row.pageUrl))||u)}
async function enrich(list){var out=[],seen={};function add(row){var u=s(row&&row.url);if(!u||seen[u])return;seen[u]=1;out.push(row)}for(var i=0;i<list.length;i++){var row=list[i];if(!row||typeof row!=="object")continue;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u)){if(c.preserveOriginal)add(row);continue}if(i<c.maxRows&&!directByName(u)){var ref=refererOf(row,u),jar=[],found=await resolve(u,row,ref,0,{},jar);for(var j=0;j<found.length;j++)add(clone(row,found[j]))}add(row)}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalMediaEnrichmentV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var list=await enrich(x.list);return rebuild(v,x,list)};wrap.__nuvioGlobalMediaEnrichmentV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true,"implementationRevision":"playback-context-v3"});
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:8be5413aec45 */
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
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=DEFAULT_UA;
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
    if(!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=DEFAULT_UA;has=true}
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"moviesmod","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"platform-playback-context-v3"});
