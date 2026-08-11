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
})(typeof globalThis!=="undefined"?globalThis:this,[["YWxsbW92aWVsYW5kLm9uZQ==","allmovieland.art"],["YWxsbW92aWVsYW5kLnlvdQ==","allmovieland.art"]]);
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
})(typeof globalThis!=="undefined"?globalThis:this,"W3siY2FuZGlkYXRlcyI6WyJodHRwczovL2FsbG1vdmllbGFuZC5hcnQiXSwiaG9zdHMiOlsiYWxsbW92aWVsYW5kLnlvdSJdfSx7ImNhbmRpZGF0ZXMiOlsiaHR0cHM6Ly9hbGxtb3ZpZWxhbmQuYXJ0Il0sImhvc3RzIjpbImFsbG1vdmllbGFuZC5vbmUiXX1d");
/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */

const _0x585d93=_0x1535;(function(_0x5bc967,_0x4704d9){const _0x240f7e=_0x1535,_0x5dfe66=_0x5bc967();while(!![]){try{const _0x34ac68=-parseInt(_0x240f7e(0xab))/0x1*(-parseInt(_0x240f7e(0xd0))/0x2)+parseInt(_0x240f7e(0xc4))/0x3*(parseInt(_0x240f7e(0xaa))/0x4)+parseInt(_0x240f7e(0x98))/0x5+parseInt(_0x240f7e(0xdb))/0x6+-parseInt(_0x240f7e(0x87))/0x7+-parseInt(_0x240f7e(0xe6))/0x8*(-parseInt(_0x240f7e(0xaf))/0x9)+-parseInt(_0x240f7e(0x8f))/0xa*(parseInt(_0x240f7e(0xa2))/0xb);if(_0x34ac68===_0x4704d9)break;else _0x5dfe66['push'](_0x5dfe66['shift']());}catch(_0x122c06){_0x5dfe66['push'](_0x5dfe66['shift']());}}}(_0x1ca4,0xda8b3));var __create=Object[_0x585d93(0x8d)],__defProp=Object[_0x585d93(0x96)],__defProps=Object['defineProperties'],__getOwnPropDesc=Object[_0x585d93(0xb1)],__getOwnPropDescs=Object[_0x585d93(0xcf)],__getOwnPropNames=Object[_0x585d93(0xcb)],__getOwnPropSymbols=Object[_0x585d93(0xa6)],__getProtoOf=Object[_0x585d93(0xac)],__hasOwnProp=Object[_0x585d93(0xb0)][_0x585d93(0x88)],__propIsEnum=Object['prototype'][_0x585d93(0x93)],__defNormalProp=(_0x2272e3,_0xab69db,_0x2d1cea)=>_0xab69db in _0x2272e3?__defProp(_0x2272e3,_0xab69db,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x2d1cea}):_0x2272e3[_0xab69db]=_0x2d1cea,__spreadValues=(_0x4bc988,_0x51d5a0)=>{const _0x535d00=_0x585d93;for(var _0x121b6c in _0x51d5a0||(_0x51d5a0={}))if(__hasOwnProp[_0x535d00(0xe7)](_0x51d5a0,_0x121b6c))__defNormalProp(_0x4bc988,_0x121b6c,_0x51d5a0[_0x121b6c]);if(__getOwnPropSymbols)for(var _0x121b6c of __getOwnPropSymbols(_0x51d5a0)){if(__propIsEnum[_0x535d00(0xe7)](_0x51d5a0,_0x121b6c))__defNormalProp(_0x4bc988,_0x121b6c,_0x51d5a0[_0x121b6c]);}return _0x4bc988;},__spreadProps=(_0x2408c2,_0x231be8)=>__defProps(_0x2408c2,__getOwnPropDescs(_0x231be8)),__copyProps=(_0x49facb,_0x5a8e9a,_0x4cb84b,_0x5de8ad)=>{const _0xee573a=_0x585d93;if(_0x5a8e9a&&typeof _0x5a8e9a===_0xee573a(0x9c)||typeof _0x5a8e9a===_0xee573a(0xc1)){for(let _0x549c2a of __getOwnPropNames(_0x5a8e9a))if(!__hasOwnProp['call'](_0x49facb,_0x549c2a)&&_0x549c2a!==_0x4cb84b)__defProp(_0x49facb,_0x549c2a,{'get':()=>_0x5a8e9a[_0x549c2a],'enumerable':!(_0x5de8ad=__getOwnPropDesc(_0x5a8e9a,_0x549c2a))||_0x5de8ad[_0xee573a(0xb5)]});}return _0x49facb;},__toESM=(_0x2bf915,_0x453623,_0x3b6817)=>(_0x3b6817=_0x2bf915!=null?__create(__getProtoOf(_0x2bf915)):{},__copyProps(_0x453623||!_0x2bf915||!_0x2bf915[_0x585d93(0xce)]?__defProp(_0x3b6817,_0x585d93(0xda),{'value':_0x2bf915,'enumerable':!![]}):_0x3b6817,_0x2bf915)),__async=(_0x3be590,_0x2163a4,_0x206f1d)=>{return new Promise((_0x21fad8,_0x177450)=>{const _0x24bbdc=_0x1535;var _0x59b2f7=_0x39c5f8=>{const _0x13220e=_0x1535;try{_0x24c22d(_0x206f1d[_0x13220e(0x91)](_0x39c5f8));}catch(_0x2e2a51){_0x177450(_0x2e2a51);}},_0x1c9322=_0x47bf87=>{const _0x1092ad=_0x1535;try{_0x24c22d(_0x206f1d[_0x1092ad(0xbb)](_0x47bf87));}catch(_0x2c4275){_0x177450(_0x2c4275);}},_0x24c22d=_0x1b6dbd=>_0x1b6dbd['done']?_0x21fad8(_0x1b6dbd['value']):Promise['resolve'](_0x1b6dbd[_0x24bbdc(0x8c)])['then'](_0x59b2f7,_0x1c9322);_0x24c22d((_0x206f1d=_0x206f1d['apply'](_0x3be590,_0x2163a4))[_0x24bbdc(0x91)]());});},import_cheerio_without_node_native=__toESM(require(_0x585d93(0xa0))),TMDB_API_KEY=_0x585d93(0xb3),TMDB_BASE_URL=_0x585d93(0xdc),MAIN_URL='https://allmovieland.art',HEADERS={'User-Agent':_0x585d93(0xd6),'Accept':_0x585d93(0xc8),'Accept-Language':_0x585d93(0xe4)};function _0x1ca4(){const _0x5e6a46=['l3bSyxLSAxn0lW','w0fSBe1VDMLLtgfUzf0GtM8GCdmGsLnptIbMB3vUzcbPBIbLBwjLzc4','r0vu','mta1odHiDwjszxy','ntqZody5AvfnrMXQ','z2v0uhjVDg90ExbLt2y','Dgv4Da','lNr4Da','ouHNvef0qW','ChjVDg90ExbL','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9Y','AgfZ','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','yM9KEsa+ihnJCMLWDa','zw51BwvYywjSzq','w0fSBe1VDMLLtgfUzf0Gq291BgqGBM90igzPBMqGCgXHEwvYigrVBwfPBIbVCIbjrc4','zxjYB3i','zxH0zxjUywXFAwrZ','vw5RBM93BG','BMfTzq','DgHYB3C','qwXStw92Awvmyw5Kic0G','Bg9Hza','Bwf0y2G','BwfW','Aw1KyL9Pza','zNvUy3rPB24','kd88pvWOkvTCzcHCxv0Rkd89xcKP','zxHWB3j0CW','mtuYneHLsxnoBq','C3bSAxq','iIaO','AhrTBa','Dgv4Dc9ODg1SlgfWCgXPy2f0Aw9Ul3HODg1Sk3HTBcXHChbSAwnHDgLVBI94BwW7Ct0WlJKSAw1Hz2uVyxzPzIXPBwfNzs93zwjWlcOVkJTXptaUoa','w0fSBe1VDMLLtgfUzf0Gve1eqIbjBMzVoIaI','zgL2lNrHyNnFx2nVBNrLBNqGC2nYAxb0','z2v0t3DUuhjVCgvYDhLoyw1LCW','qwXStw92Awvmyw5K','EwvHCG','x19LC01VzhvSzq','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','mKH5CfrqyG','BgvUz3rO','AhjLzG','zM9SzgvY','yxr0CG','C3rHCNrZv2L0Aa','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeZnY4WlJaUmcbtywzHCMKVntm3lJm2','zMLYC3rFywLYx2rHDgu','zMLUza','Bw92Awu','zgvMyxvSDa','otqXmZGZohPxDK9qsa','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmW','zMLSDgvY','zwfJAa','w0fSBe1VDMLLtgfUzf0GrMv0y2HPBMCGC3rYzwfTCYbMB3iGve1eqIbjrdOG','yxbWBgLJyxrPB24VANnVBG','zMLSzq','ysa+igGZ','l2LUzgv4lNbOCd9ZDg9YEt0','zw4TvvmSzw47Ct0WlJu','C2L6zq','mtK0nJq4ogXxuxfhzG','y2fSBa','Bg9N','ywXS','ywXSBw92AwvSyw5K','jMrVpxnLyxjJAczZDwjHy3rPB249C2vHCMnO','CMvWBgfJzq','nZG1mdm3nevMwfDkwa','AgfZt3DUuhjVCgvYDhK','CMvSzwfZzv9KyxrL','w0fSBe1VDMLLtgfUzf0GtM8GC3rYzwfTCYbMB3vUzcbMB3iGDgHLihjLCxvLC3rLzcbTzwrPys4','ChvZAa','DMfSDwu','y3jLyxrL','zxbPC29Kzq','mtm3nZa0mtboAwHxCMO','yxj0AwnSzs5ZAg9YDc1TAwq','BMv4Da','A2v5','ChjVCgvYDhLjC0vUDw1LCMfIBgu','w0fSBe1VDMLLtgfUzf0GrMfPBgvKihrVigv4DhjHy3qGC3rYzwfToIa','w0fSBe1VDMLLtgfUzf0Gu2vSzwn0zwq6ici','zgvMAw5LuhjVCgvYDhK','p2fWAv9RzxK9','ntm0otq1mfjkDMDvuW','Ahr0Ca','DhjPBq','tI9b','B2jQzwn0','DgL0Bgu','zxzLCNK','CgfYC2u','y2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzL','vxnLCI1bz2vUDa','mJjTyvbbD0q','BgfZDa','BwvZC2fNzq','ue9tva','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ'];_0x1ca4=function(){return _0x5e6a46;};return _0x1ca4();}function getTMDBDetails(_0x2aebb6,_0x12d1ab){return __async(this,null,function*(){const _0xc42d13=_0x1535;var _0x4b6787;const _0x88c99f=_0x12d1ab==='tv'?'tv':_0xc42d13(0xd9),_0x36c80f=TMDB_BASE_URL+'/'+_0x88c99f+'/'+_0x2aebb6+_0xc42d13(0x97)+TMDB_API_KEY+'&append_to_response=external_ids',_0x3f44a0=yield fetch(_0x36c80f,{'method':_0xc42d13(0xa9),'headers':{'Accept':_0xc42d13(0xe0),'User-Agent':'Mozilla/5.0'}});if(!_0x3f44a0['ok'])throw new Error('TMDB\x20API\x20error:\x20'+_0x3f44a0['status']);const _0x1c16a5=yield _0x3f44a0['json'](),_0x4fe47f=_0x12d1ab==='tv'?_0x1c16a5[_0xc42d13(0xba)]:_0x1c16a5['title'],_0x4b9608=_0x12d1ab==='tv'?_0x1c16a5[_0xc42d13(0xd7)]:_0x1c16a5[_0xc42d13(0x89)],_0x5d5561=_0x4b9608?parseInt(_0x4b9608[_0xc42d13(0xc5)]('-')[0x0]):null;return{'title':_0x4fe47f,'year':_0x5d5561,'imdbId':((_0x4b6787=_0x1c16a5[_0xc42d13(0xb8)])==null?void 0x0:_0x4b6787[_0xc42d13(0xc0)])||null,'data':_0x1c16a5};});}function normalizeTitle(_0x40dc60){const _0x27878f=_0x585d93;if(!_0x40dc60)return'';return _0x40dc60['toLowerCase']()[_0x27878f(0x86)](/\b(the|a|an)\b/g,'')[_0x27878f(0x86)](/[:\-_]/g,'\x20')[_0x27878f(0x86)](/\s+/g,'\x20')['replace'](/[^\w\s]/g,'')[_0x27878f(0x9a)]();}function calculateTitleSimilarity(_0x2700af,_0x2844df){const _0x4d1634=_0x585d93,_0x2754bb=normalizeTitle(_0x2700af),_0x2228a7=normalizeTitle(_0x2844df);if(_0x2754bb===_0x2228a7)return 0x1;const _0x316f42=_0x2754bb[_0x4d1634(0xc5)](/\s+/)[_0x4d1634(0xdd)](_0x52a881=>_0x52a881[_0x4d1634(0xd1)]>0x0),_0x2b902d=_0x2228a7['split'](/\s+/)[_0x4d1634(0xdd)](_0x5f008e=>_0x5f008e[_0x4d1634(0xd1)]>0x0);if(_0x316f42[_0x4d1634(0xd1)]===0x0||_0x2b902d[_0x4d1634(0xd1)]===0x0)return 0x0;const _0x1fcca6=new Set(_0x316f42),_0x2f4a0d=new Set(_0x2b902d),_0x3912f4=_0x316f42[_0x4d1634(0xdd)](_0x338654=>_0x2f4a0d[_0x4d1634(0xb2)](_0x338654)),_0x3232a5=new Set([..._0x316f42,..._0x2b902d]),_0x12e40d=_0x3912f4[_0x4d1634(0xd1)]/_0x3232a5[_0x4d1634(0xe5)],_0x114b72=_0x2b902d[_0x4d1634(0xdd)](_0x12bdf3=>!_0x1fcca6[_0x4d1634(0xb2)](_0x12bdf3))[_0x4d1634(0xd1)];let _0x1153bc=_0x12e40d-_0x114b72*0.05;return _0x316f42[_0x4d1634(0xd1)]>0x0&&_0x316f42[_0x4d1634(0x9e)](_0x451666=>_0x2f4a0d[_0x4d1634(0xb2)](_0x451666))&&(_0x1153bc+=0.2),_0x1153bc;}function findBestTitleMatch(_0x1a9474,_0x45cfa2){const _0x5af6a3=_0x585d93;if(!_0x45cfa2||_0x45cfa2['length']===0x0)return null;let _0x506ece=null,_0xddfc75=0x0;for(const _0x3f31e9 of _0x45cfa2){let _0x5f02cd=calculateTitleSimilarity(_0x1a9474['title'],_0x3f31e9[_0x5af6a3(0x9d)]);if(_0x1a9474[_0x5af6a3(0xcd)]&&_0x3f31e9[_0x5af6a3(0xcd)]){const _0x255d12=Math['abs'](_0x1a9474['year']-_0x3f31e9[_0x5af6a3(0xcd)]);if(_0x255d12===0x0)_0x5f02cd+=0.2;else{if(_0x255d12<=0x1)_0x5f02cd+=0.1;else{if(_0x255d12>0x5)_0x5f02cd-=0.3;}}}_0x5f02cd>_0xddfc75&&_0x5f02cd>0.3&&(_0xddfc75=_0x5f02cd,_0x506ece=_0x3f31e9);}return _0x506ece;}function _0x1535(_0x27e78a,_0xcd143){_0x27e78a=_0x27e78a-0x86;const _0x1ca48d=_0x1ca4();let _0x1535ac=_0x1ca48d[_0x27e78a];if(_0x1535['XSMvjz']===undefined){var _0x5b699d=function(_0x1fbf4e){const _0x24ca80='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x2272e3='',_0xab69db='';for(let _0x2d1cea=0x0,_0x4bc988,_0x51d5a0,_0x121b6c=0x0;_0x51d5a0=_0x1fbf4e['charAt'](_0x121b6c++);~_0x51d5a0&&(_0x4bc988=_0x2d1cea%0x4?_0x4bc988*0x40+_0x51d5a0:_0x51d5a0,_0x2d1cea++%0x4)?_0x2272e3+=String['fromCharCode'](0xff&_0x4bc988>>(-0x2*_0x2d1cea&0x6)):0x0){_0x51d5a0=_0x24ca80['indexOf'](_0x51d5a0);}for(let _0x2408c2=0x0,_0x231be8=_0x2272e3['length'];_0x2408c2<_0x231be8;_0x2408c2++){_0xab69db+='%'+('00'+_0x2272e3['charCodeAt'](_0x2408c2)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0xab69db);};_0x1535['UvLulp']=_0x5b699d,_0x1535['sqlSnP']={},_0x1535['XSMvjz']=!![];}const _0x1a041b=_0x1ca48d[0x0],_0x4159fb=_0x27e78a+_0x1a041b,_0x961c0=_0x1535['sqlSnP'][_0x4159fb];return!_0x961c0?(_0x1535ac=_0x1535['UvLulp'](_0x1535ac),_0x1535['sqlSnP'][_0x4159fb]=_0x1535ac):_0x1535ac=_0x961c0,_0x1535ac;}function getStreams(_0x557378,_0x5e7559=_0x585d93(0xd9),_0x2c24f0=null,_0xa15d0c=null){return __async(this,null,function*(){const _0x4b221f=_0x1535;console[_0x4b221f(0xe8)](_0x4b221f(0xdf)+_0x557378+',\x20Type:\x20'+_0x5e7559);try{const _0x4120bf=yield getTMDBDetails(_0x557378,_0x5e7559);console['log'](_0x4b221f(0xc9)+_0x4120bf[_0x4b221f(0x9d)]+'\x22\x20('+(_0x4120bf[_0x4b221f(0xcd)]||_0x4b221f(0x9b))+')');const _0x17e515=_0x4120bf[_0x4b221f(0x9d)],_0x4e358c=MAIN_URL+_0x4b221f(0xe3)+encodeURIComponent(_0x17e515)+_0x4b221f(0xeb),_0x59312e=yield fetch(_0x4e358c,{'headers':HEADERS}),_0x3908e7=yield _0x59312e[_0x4b221f(0xad)](),_0x54f259=import_cheerio_without_node_native[_0x4b221f(0xda)][_0x4b221f(0xbd)](_0x3908e7),_0x186d64=[];_0x54f259(_0x4b221f(0x90))[_0x4b221f(0xde)]((_0x3e65f7,_0xc5f9f2)=>{const _0x504c80=_0x4b221f,_0x3c7620=_0x54f259(_0xc5f9f2)[_0x504c80(0xd8)](_0x504c80(0xe2))['text']()[_0x504c80(0x9a)](),_0x256940=_0x54f259(_0xc5f9f2)[_0x504c80(0xd8)]('a')[_0x504c80(0xd4)]('href'),_0x5e0f21=_0x3c7620['match'](new RegExp(_0x504c80(0xc2))),_0x4e2544=_0x5e0f21?parseInt(_0x5e0f21[0x0]):null;_0x186d64[_0x504c80(0x8b)]({'title':_0x3c7620,'href':_0x256940,'year':_0x4e2544});});if(_0x186d64[_0x4b221f(0xd1)]===0x0)return console[_0x4b221f(0xe8)]('[AllMovieLand]\x20No\x20search\x20results\x20found.'),[];const _0x3bb101=findBestTitleMatch(_0x4120bf,_0x186d64),_0x34e089=_0x3bb101||_0x186d64[0x0];console[_0x4b221f(0xe8)](_0x4b221f(0x95)+_0x34e089[_0x4b221f(0x9d)]+_0x4b221f(0xc6)+_0x34e089[_0x4b221f(0xd2)]+')');const _0x450560=yield fetch(_0x34e089[_0x4b221f(0xd2)],{'headers':HEADERS}),_0x36ade9=yield _0x450560[_0x4b221f(0xad)](),_0x16773f=import_cheerio_without_node_native[_0x4b221f(0xda)]['load'](_0x36ade9),_0x1eb60e=_0x16773f(_0x4b221f(0xca))[_0x4b221f(0xc7)]()||'',_0x17503d=_0x1eb60e[_0x4b221f(0xbe)](/const AwsIndStreamDomain\s*=\s*'([^']+)'/),_0x3058d2=_0x17503d?_0x17503d[0x1][_0x4b221f(0x86)](/\/$/,''):null,_0x78315c=_0x1eb60e[_0x4b221f(0xbe)](/src:\s*'([^']+)'/),_0x5c2c01=_0x78315c?_0x78315c[0x1]:null;if(!_0x3058d2||!_0x5c2c01)return console[_0x4b221f(0xe8)](_0x4b221f(0xb6)),[];const _0x57c41d=_0x3058d2+'/play/'+_0x5c2c01,_0x3d0b4b=yield fetch(_0x57c41d,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x34e089['href']})}),_0x439dc4=yield _0x3d0b4b[_0x4b221f(0xad)](),_0x3004ae=import_cheerio_without_node_native[_0x4b221f(0xda)][_0x4b221f(0xbd)](_0x439dc4),_0x56742f=_0x3004ae(_0x4b221f(0xb4))[_0x4b221f(0xa3)]()[_0x4b221f(0xc7)]()||'',_0x539e26=_0x56742f[_0x4b221f(0xbe)](/let\s+p3\s*=\s*(\{.*\});/);if(!_0x539e26)return console[_0x4b221f(0xe8)](_0x4b221f(0xa8)),[];const _0x351c54=JSON[_0x4b221f(0x9f)](_0x539e26[0x1]);let _0x3b59e0=_0x351c54[_0x4b221f(0xe1)]['replace'](/\\\//g,'/');if(!_0x3b59e0[_0x4b221f(0xd5)](_0x4b221f(0x99)))_0x3b59e0=''+_0x3058d2+_0x3b59e0;const _0x3ad049=yield fetch(_0x3b59e0,{'method':_0x4b221f(0xa5),'headers':__spreadProps(__spreadValues({},HEADERS),{'X-CSRF-TOKEN':_0x351c54[_0x4b221f(0x92)],'Referer':_0x57c41d})}),_0x48b3a6=yield _0x3ad049[_0x4b221f(0xad)]();let _0x267f03=[];const _0x20ddc1=JSON[_0x4b221f(0x9f)](_0x48b3a6[_0x4b221f(0x86)](/,\]/g,']'));if(_0x5e7559===_0x4b221f(0xd9))_0x267f03=_0x20ddc1[_0x4b221f(0xdd)](_0x21c86c=>_0x21c86c&&_0x21c86c['file']);else{if(_0x5e7559==='tv'){const _0x2332d6=_0x20ddc1['find'](_0x4e06e5=>_0x4e06e5['id']==_0x2c24f0);if(_0x2332d6&&_0x2332d6[_0x4b221f(0xd3)]){const _0x445e05=_0x2332d6[_0x4b221f(0xd3)][_0x4b221f(0xd8)](_0x18558c=>_0x18558c[_0x4b221f(0x8e)]==_0xa15d0c);_0x445e05&&_0x445e05[_0x4b221f(0xd3)]&&(_0x267f03=_0x445e05['folder'][_0x4b221f(0xdd)](_0x714d85=>_0x714d85&&_0x714d85[_0x4b221f(0xe1)]));}}}if(_0x267f03[_0x4b221f(0xd1)]===0x0)return console[_0x4b221f(0xe8)](_0x4b221f(0x8a)),[];const _0x4742a2=[];return yield Promise[_0x4b221f(0xe9)](_0x267f03[_0x4b221f(0xbf)](_0x4cac34=>__async(this,null,function*(){const _0x4589ca=_0x4b221f;try{const _0x18efde=_0x4cac34[_0x4589ca(0xe1)][_0x4589ca(0x86)](/^~/,''),_0x2e0e93=_0x3058d2+_0x4589ca(0xa7)+_0x18efde+_0x4589ca(0xae),_0x3d19f2=yield fetch(_0x2e0e93,{'method':_0x4589ca(0xa5),'headers':__spreadProps(__spreadValues({},HEADERS),{'X-CSRF-TOKEN':_0x351c54[_0x4589ca(0x92)],'Referer':_0x57c41d})}),_0x171484=(yield _0x3d19f2['text']())[_0x4589ca(0x9a)]();if(_0x171484&&_0x171484[_0x4589ca(0xd5)](_0x4589ca(0x99))){const _0x5a4747=_0x4cac34[_0x4589ca(0x9d)]||_0x4589ca(0xb9);_0x4742a2[_0x4589ca(0x8b)]({'name':_0x4589ca(0xcc),'title':_0x4589ca(0xbc)+_0x5a4747,'url':_0x171484,'quality':_0x5a4747,'headers':{'Referer':_0x3058d2+'/','Origin':_0x3058d2,'User-Agent':HEADERS[_0x4589ca(0xa1)]},'provider':_0x4589ca(0xea)});}}catch(_0x21d4de){console[_0x4589ca(0xb7)](_0x4589ca(0x94)+_0x21d4de[_0x4589ca(0xa4)]);}}))),_0x4742a2;}catch(_0x2c0cf5){return console[_0x4b221f(0xb7)]('[AllMovieLand]\x20Error:\x20'+_0x2c0cf5['message']),[];}});}module[_0x585d93(0xc3)]={'getStreams':getStreams};

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
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1:91755789b56e */
;(function(g,c){"use strict";
var TMDB_KEY="8265bd1679663a7ea12ac168da84d2e8";
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function norm(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return norm(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function unique(values){var out=[],seen={};(values||[]).forEach(function(v){v=s(v).replace(/\s*\(\d{4}\)\s*$/,"");var k=norm(v);if(v&&k&&!seen[k]){seen[k]=1;out.push(v)}});return out}
function args(a){var first=a[0],q=first&&typeof first==="object"&&!Array.isArray(first)?Object.assign({},first):{tmdbId:first,mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||q.category||"movie").toLowerCase();q.season=Number(q.season)||0;q.episode=Number(q.episode)||0;return q}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
async function request(url,json,referer){try{var h={Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,*/*","Accept-Language":"fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"};if(referer){h.Referer=referer;try{h.Origin=new URL(referer).origin}catch(_){}}var r=await g.fetch(url,{headers:h,redirect:"follow",signal:timeout()});if(!r||!r.ok)return null;return {url:s(r.url||url),body:json?await r.json():await r.text(),type:r.headers&&r.headers.get?r.headers.get("content-type"):""}}catch(_){return null}}
function kindFor(q){if(q.mediaType==="tv")return"tv";if(q.mediaType==="anime"&&q.season&&q.episode)return"tv";return"movie"}
async function meta(q){var titles=unique([q.title,q.name,q.label,q.settings&&q.settings.title]),year=Number(q.year||q.settings&&q.settings.year)||0,kind=kindFor(q);if(q.tmdbId){var urls=["https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+TMDB_KEY+"&language=fr-FR","https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+TMDB_KEY+"&language=en-US"];for(var i=0;i<urls.length;i++){var r=await request(urls[i],true);if(r&&r.body){var d=r.body;titles=unique(titles.concat([d.title,d.name,d.original_title,d.original_name]));var date=s(d.release_date||d.first_air_date);year=year||Number(date.slice(0,4))||0}}var alt=await request("https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"/alternative_titles?api_key="+TMDB_KEY,true);if(alt&&alt.body){var rows=alt.body.titles||alt.body.results||[];rows.slice(0,30).forEach(function(x){if(x&&["FR","US","GB","CA","DK"].indexOf(String(x.iso_3166_1||"").toUpperCase())>=0)titles.push(x.title)});titles=unique(titles)}}return{titles:titles.slice(0,c.maxAliases),year:year,tmdbId:q.tmdbId}}
function tokens(v){var noise={the:1,a:1,an:1,le:1,la:1,les:1,un:1,une:1,de:1,des:1,du:1,and:1,et:1,film:1,movie:1,streaming:1,watch:1,voir:1,regarder:1};return norm(v).split(" ").filter(function(x){return x.length>1&&!noise[x]&&!/^\d{4}$/.test(x)})}
function aliasScore(text,m){var n=norm(text),best=-1;(m.titles||[]).forEach(function(t){var nt=norm(t),want=tokens(t);if(!want.length)return;var score=n.indexOf(nt)>=0?120:0;if(!score&&want.every(function(x){return n.indexOf(x)>=0}))score=90;if(score>best)best=score});if(best<0)return-1;var years=n.match(/\b(?:19|20)\d{2}\b/g)||[];if(m.year&&years.length&&years.indexOf(String(m.year))<0)return-1;if(m.year&&n.indexOf(String(m.year))>=0)best+=15;return best}
function links(html,base,m){var rows=[],seen={},re=/<a\b([^>]*)href=["']([^"']+)["']([^>]*)>([\s\S]*?)<\/a>/gi,x;while((x=re.exec(String(html||"")))!==null){var u=abs(x[2],base),label=(s(x[1])+" "+s(x[3])+" "+s(x[4]).replace(/<[^>]+>/g," "));if(!u||seen[u])continue;seen[u]=1;var score=aliasScore(label+" "+u,m);if(score>=90)rows.push({url:u,score:score})}return rows.sort(function(a,b){return b.score-a.score}).slice(0,c.maxCandidates)}
function mediaish(u){return /(?:\.m3u8|\.mpd|\.mp4|\.mkv|\.webm)(?:[?#]|$)|\/(?:embed|player|watch|stream|video)(?:[/?#.-]|$)|\/e\//i.test(u)}
function extractPlayers(html,base,q){var text=String(html||"").replace(/\\\//g,"/"),out=[],seen={};function add(v){var u=abs(v,base);if(!u||seen[u]||!/^https?:\/\//i.test(u)||!mediaish(u))return;seen[u]=1;out.push(u)}var scoped=text;if((q.mediaType==="tv"||q.mediaType==="anime")&&q.season&&q.episode){var patterns=[new RegExp("s(?:aison|eason)?[ ._-]*0?"+q.season+"[ ._-]*e(?:p(?:isode)?)?[ ._-]*0?"+q.episode,"i"),new RegExp("(?:episode|ep)[ ._-]*0?"+q.episode,"i")],chunks=text.split(/(?=<[^>]+(?:episode|season|saison|data-ep))/i).filter(function(x){return patterns.some(function(p){return p.test(x)})});if(chunks.length)scoped=chunks.join("\n");else return[]}var patterns2=[/(?:src|href|data-src|data-url|data-embed|data-player|data-video|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi],m;for(var i=0;i<patterns2.length;i++){patterns2[i].lastIndex=0;while((m=patterns2[i].exec(scoped))!==null){add(m[1]);if(out.length>=c.maxPlayers)return out}}return out}
function rows(urls,m,page){return urls.slice(0,c.maxPlayers).map(function(u,i){var out={name:c.providerName+(urls.length>1?" #"+(i+1):""),title:c.providerName+" - "+(m.titles[0]||"Media"),url:u,quality:"Unknown",headers:{Referer:page,Origin:(function(){try{return new URL(page).origin}catch(_){return c.baseUrl}})()}};if(c.languageHint)out.language=c.languageHint;if(/\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)/i.test(u))out.isDirect=true;return out})}
async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return[];var m=await meta(q);if(!m.titles.length)return[];var candidates=[],searches=[];m.titles.forEach(function(t){candidates.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&candidates.length<c.maxCandidates*4;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)candidates=candidates.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}candidates=unique(candidates).slice(0,c.maxCandidates);for(var j=0;j<candidates.length;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!new RegExp("tmdb[^0-9]{0,24}"+String(m.tmdbId||"$^"),"i").test(String(page.body||"")))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV1)return false;var native=o[k];var wrap=async function(){var v;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v);if(x&&x.list.length)return v;var recovered=await recover(args(arguments));if(!recovered.length)return v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://allmovieland.art","providerName":"allmovieland","maxAliases":6,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"languageHint":""});
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
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:29f19ecf1e09 */
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
async function recover(q){if(["movie","tv","anime"].indexOf(q.mediaType)<0)return[];var m=await meta(q);if(!m.titles.length)return[];var candidates=[],searches=[];m.titles.forEach(function(t){candidates.push(c.baseUrl+"/"+slug(t));searches.push(c.baseUrl+"/?s="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?q="+encodeURIComponent(t));searches.push(c.baseUrl+"/search?query="+encodeURIComponent(t))});for(var i=0;i<searches.length&&candidates.length<c.maxCandidates*4;i++){var sr=await request(searches[i],false,c.baseUrl+"/");if(sr)candidates=candidates.concat(links(sr.body,sr.url,m).map(function(x){return x.url}))}candidates=unique(candidates).slice(0,c.maxCandidates);for(var j=0;j<candidates.length;j++){var page=await request(candidates[j],false,c.baseUrl+"/");if(!page)continue;var identity=aliasScore(page.url+" "+String(page.body||"").slice(0,180000),m);if(identity<90&&!idEvidence(page.body,m))continue;var p=extractPlayers(page.body,page.url,q);if(p.length)return rows(p,m,page.url)}return[]}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalCatalogueAliasV2)return false;var native=o[k];var wrap=async function(){var v;try{v=await native.apply(this,arguments)}catch(_){v=[]}var x=slot(v);if(x&&x.list.length)return v;var recovered=await recover(args(arguments));if(!recovered.length)return v;return x?rebuild(v,x,recovered):recovered};wrap.__nuvioGlobalCatalogueAliasV2=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://allmovieland.art","providerName":"allmovieland","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"languageHint":""});
