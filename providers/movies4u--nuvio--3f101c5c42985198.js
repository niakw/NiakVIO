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
})(typeof globalThis!=="undefined"?globalThis:this,[["bTR1cGxheS5zdG9yZQ==","new3.movies4u.clinic"],["bmV3Mi5tb3ZpZXM0dS5jbGluaWM=","new3.movies4u.clinic"]]);
function _0x37fa(_0x22f59c,_0x479315){_0x22f59c=_0x22f59c-0x1c9;const _0x25521e=_0x2552();let _0x37fadc=_0x25521e[_0x22f59c];if(_0x37fa['hHrrNH']===undefined){var _0x151a66=function(_0x2dcfbf){const _0x3a07eb='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x795e0a='',_0x541483='';for(let _0x526309=0x0,_0x2f28cc,_0x11c7c9,_0x8ffaa1=0x0;_0x11c7c9=_0x2dcfbf['charAt'](_0x8ffaa1++);~_0x11c7c9&&(_0x2f28cc=_0x526309%0x4?_0x2f28cc*0x40+_0x11c7c9:_0x11c7c9,_0x526309++%0x4)?_0x795e0a+=String['fromCharCode'](0xff&_0x2f28cc>>(-0x2*_0x526309&0x6)):0x0){_0x11c7c9=_0x3a07eb['indexOf'](_0x11c7c9);}for(let _0x14edc8=0x0,_0x3e6723=_0x795e0a['length'];_0x14edc8<_0x3e6723;_0x14edc8++){_0x541483+='%'+('00'+_0x795e0a['charCodeAt'](_0x14edc8)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x541483);};_0x37fa['IrXlBK']=_0x151a66,_0x37fa['NQXPIT']={},_0x37fa['hHrrNH']=!![];}const _0x3b0499=_0x25521e[0x0],_0x1032d3=_0x22f59c+_0x3b0499,_0x470035=_0x37fa['NQXPIT'][_0x1032d3];return!_0x470035?(_0x37fadc=_0x37fa['IrXlBK'](_0x37fadc),_0x37fa['NQXPIT'][_0x1032d3]=_0x37fadc):_0x37fadc=_0x470035,_0x37fadc;}const _0x2704d0=_0x37fa;(function(_0x3373ce,_0x565226){const _0x10785d={_0x5c6699:0x1ed,_0x31d3d1:0x23c,_0x566ca1:0x234},_0x4378ec=_0x37fa,_0x298b9a=_0x3373ce();while(!![]){try{const _0x27358c=-parseInt(_0x4378ec(_0x10785d._0x5c6699))/0x1+-parseInt(_0x4378ec(0x236))/0x2+parseInt(_0x4378ec(_0x10785d._0x31d3d1))/0x3+parseInt(_0x4378ec(0x1dd))/0x4*(-parseInt(_0x4378ec(_0x10785d._0x566ca1))/0x5)+-parseInt(_0x4378ec(0x1fb))/0x6*(-parseInt(_0x4378ec(0x214))/0x7)+-parseInt(_0x4378ec(0x1fe))/0x8*(parseInt(_0x4378ec(0x205))/0x9)+parseInt(_0x4378ec(0x1de))/0xa*(parseInt(_0x4378ec(0x22c))/0xb);if(_0x27358c===_0x565226)break;else _0x298b9a['push'](_0x298b9a['shift']());}catch(_0x5e2ebb){_0x298b9a['push'](_0x298b9a['shift']());}}}(_0x2552,0x29b84));var __defProp=Object[_0x2704d0(0x1d7)],__defProps=Object['defineProperties'],__getOwnPropDescs=Object[_0x2704d0(0x1f1)],__getOwnPropSymbols=Object['getOwnPropertySymbols'],__hasOwnProp=Object['prototype']['hasOwnProperty'],__propIsEnum=Object['prototype']['propertyIsEnumerable'],__defNormalProp=(_0x795e0a,_0x541483,_0x526309)=>_0x541483 in _0x795e0a?__defProp(_0x795e0a,_0x541483,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x526309}):_0x795e0a[_0x541483]=_0x526309,__spreadValues=(_0x2f28cc,_0x11c7c9)=>{const _0x48a55d={_0x554f3f:0x1f8},_0x256b4a=_0x2704d0;for(var _0x8ffaa1 in _0x11c7c9||(_0x11c7c9={}))if(__hasOwnProp[_0x256b4a(0x1f8)](_0x11c7c9,_0x8ffaa1))__defNormalProp(_0x2f28cc,_0x8ffaa1,_0x11c7c9[_0x8ffaa1]);if(__getOwnPropSymbols)for(var _0x8ffaa1 of __getOwnPropSymbols(_0x11c7c9)){if(__propIsEnum[_0x256b4a(_0x48a55d._0x554f3f)](_0x11c7c9,_0x8ffaa1))__defNormalProp(_0x2f28cc,_0x8ffaa1,_0x11c7c9[_0x8ffaa1]);}return _0x2f28cc;},__spreadProps=(_0x14edc8,_0x3e6723)=>__defProps(_0x14edc8,__getOwnPropDescs(_0x3e6723)),__async=(_0x1a06a2,_0x3b80bf,_0x476c80)=>{return new Promise((_0x5b4446,_0x54a678)=>{const _0x24a4fe={_0x142529:0x1d2},_0x597dfa=_0x37fa;var _0x448140=_0x3ff91f=>{try{_0x5368f8(_0x476c80['next'](_0x3ff91f));}catch(_0x567ff6){_0x54a678(_0x567ff6);}},_0x376f78=_0x1f440e=>{const _0x1ec9ff=_0x37fa;try{_0x5368f8(_0x476c80[_0x1ec9ff(_0x24a4fe._0x142529)](_0x1f440e));}catch(_0x11de21){_0x54a678(_0x11de21);}},_0x5368f8=_0x3c6241=>_0x3c6241['done']?_0x5b4446(_0x3c6241['value']):Promise['resolve'](_0x3c6241['value'])['then'](_0x448140,_0x376f78);_0x5368f8((_0x476c80=_0x476c80['apply'](_0x1a06a2,_0x3b80bf))[_0x597dfa(0x1c9)]());});},DOMAINS_URL=_0x2704d0(0x1fc),FALLBACK_URL=_0x2704d0(0x1e9),TMDB_API_KEY='1865f43a0549ca50d341dd9ab8b29f49',HUB_CLOUD_API='https://hc-zf3c.vercel.app',HEADERS={'User-Agent':_0x2704d0(0x1e7),'Referer':FALLBACK_URL,'Cookie':_0x2704d0(0x1cb)},cachedBaseUrl=null;function getBaseUrl(){return __async(this,null,function*(){const _0x4430ac=_0x37fa;if(cachedBaseUrl)return cachedBaseUrl;try{const _0x26ef23=yield fetch(DOMAINS_URL,{'skipSizeCheck':!![]}),_0x36eda8=yield _0x26ef23[_0x4430ac(0x22a)]();cachedBaseUrl=_0x36eda8[_0x4430ac(0x239)]||_0x36eda8['movies4uhd']||FALLBACK_URL;}catch(_0x53a937){cachedBaseUrl=FALLBACK_URL;}return cachedBaseUrl;});}function extractQuality(_0x247197){const _0x4079a2={_0x433961:0x204,_0x153abf:0x210,_0x38701c:0x215},_0x1c4f14=_0x2704d0,_0x132a38=(_0x247197||'')[_0x1c4f14(0x223)]();if(/\b(2160p|4k|uhd)\b/['test'](_0x132a38))return'4K';if(/\b(1080p|1080)(?!(?:\s*gb|\s*mb|\s*b))\b/[_0x1c4f14(_0x4079a2._0x433961)](_0x132a38))return'1080p';if(/\b(720p|720)(?!(?:\s*gb|\s*mb|\s*b))\b/['test'](_0x132a38))return'720p';if(/\b(480p|480)(?!(?:\s*gb|\s*mb|\s*b))\b/[_0x1c4f14(0x204)](_0x132a38))return _0x1c4f14(_0x4079a2._0x153abf);if(/\b(360p|360)(?!(?:\s*gb|\s*mb|\s*b))\b/[_0x1c4f14(0x204)](_0x132a38))return'360p';return _0x1c4f14(_0x4079a2._0x38701c);}function parseExtraMetadata(_0x1a38f5){const _0xf8c0db={_0x1c996d:0x20e,_0x1d811a:0x1cf,_0x5543b9:0x1da,_0x448ef1:0x221,_0x263b99:0x1d9,_0x4c1850:0x1ca,_0xe4aea8:0x203,_0x66e999:0x1e6,_0x285498:0x21c,_0x561d8d:0x1d8,_0x23ebbd:0x1dc,_0x2e22ab:0x235,_0x59e551:0x1e0},_0x221b34=_0x2704d0,_0x11ad37=(_0x1a38f5||'')[_0x221b34(_0xf8c0db._0x1c996d)]();let _0x5e3994=_0x221b34(0x21d);if(_0x11ad37['includes']('DUAL'))_0x5e3994=_0x221b34(_0xf8c0db._0x1d811a);if(_0x11ad37['includes'](_0x221b34(0x213))&&!_0x11ad37['includes'](_0x221b34(_0xf8c0db._0x5543b9)))_0x5e3994='English';const _0x6f4f7f=_0x11ad37['match'](/(\d+(?:\.\d+)?\s*[MGB]B)/i);let _0x40a25b=_0x6f4f7f?_0x6f4f7f[0x0]['replace'](/\s+/g,''):'N/A';if(_0x40a25b==='N/A'){const _0x2332e1=_0x11ad37['match'](/(\d+\.\d+)\s?G/);if(_0x2332e1)_0x40a25b=_0x2332e1[0x1]+'GB';}let _0x26130d='MKV';if(_0x11ad37[_0x221b34(_0xf8c0db._0x448ef1)]('MP4'))_0x26130d='MP4';if(_0x11ad37['includes']('HEVC')||_0x11ad37['includes'](_0x221b34(_0xf8c0db._0x263b99))||_0x11ad37['includes']('H265'))_0x26130d+=_0x221b34(_0xf8c0db._0x4c1850);else{if(_0x11ad37['includes']('X264')||_0x11ad37[_0x221b34(_0xf8c0db._0x448ef1)](_0x221b34(_0xf8c0db._0xe4aea8)))_0x26130d+='\x20(x264)';}const _0x3e0ed5=[];if(_0x11ad37[_0x221b34(0x221)](_0x221b34(_0xf8c0db._0x66e999)))_0x3e0ed5[_0x221b34(_0xf8c0db._0x285498)](_0x221b34(_0xf8c0db._0x66e999));if(_0x11ad37['includes'](_0x221b34(_0xf8c0db._0x561d8d))||_0x11ad37[_0x221b34(0x221)]('DV')||_0x11ad37['includes']('VISION')||_0x11ad37['includes'](_0x221b34(0x21b))||_0x11ad37[_0x221b34(_0xf8c0db._0x448ef1)]('DD5'))_0x3e0ed5['push'](_0x221b34(_0xf8c0db._0x23ebbd));if(_0x11ad37['includes']('10BIT'))_0x3e0ed5[_0x221b34(0x21c)](_0x221b34(0x209));if(_0x11ad37['includes']('REMUX'))_0x3e0ed5['push']('Remux');return{'language':_0x5e3994,'size':_0x40a25b,'format':_0x26130d,'extras':_0x3e0ed5[_0x221b34(_0xf8c0db._0x2e22ab)]>0x0?_0x3e0ed5['join']('\x20|\x20'):_0x221b34(_0xf8c0db._0x59e551)};}function cleanServerName(_0x1bea5c){const _0x2e92fc={_0x4e2773:0x220,_0x3c54d9:0x231,_0x23b4c0:0x1fd},_0x59dec6=_0x2704d0;if(!_0x1bea5c)return _0x59dec6(0x1d0);let _0x4aa532=_0x1bea5c[_0x59dec6(0x223)]();if(_0x4aa532['includes'](_0x59dec6(0x1ce))||_0x4aa532['includes']('fast'))return _0x59dec6(0x1f0);if(_0x4aa532['includes']('pixel'))return'PixelDrain';if(_0x4aa532['includes']('drive')||_0x4aa532[_0x59dec6(0x221)](_0x59dec6(_0x2e92fc._0x4e2773)))return'Cloud\x20Drive';return _0x4aa532=_0x4aa532['replace'](/download|links?|button|server|\s+/gi,'\x20')['trim'](),_0x4aa532=_0x4aa532['replace'](/[\[\]\(\)]/g,'')[_0x59dec6(_0x2e92fc._0x3c54d9)](),_0x4aa532[_0x59dec6(_0x2e92fc._0x23b4c0)]('\x20')[_0x59dec6(0x1fa)](_0x3f9c97=>_0x3f9c97['charAt'](0x0)[_0x59dec6(0x20e)]()+_0x3f9c97['slice'](0x1))['join']('\x20')+'\x20Server';}function resolveAllHubCloudLinks(_0x3398ef){const _0xb51b9={_0x13f8b9:0x216,_0x5e844d:0x1eb};return __async(this,null,function*(){const _0x3ce4a9=_0x37fa;try{const _0x34eef2=HUB_CLOUD_API+_0x3ce4a9(_0xb51b9._0x13f8b9)+encodeURIComponent(_0x3398ef),_0x4c80a5=yield fetch(_0x34eef2,{'headers':{'Accept':_0x3ce4a9(0x1d6)},'skipSizeCheck':!![]}),_0x47262a=yield _0x4c80a5['json']();if(_0x47262a&&_0x47262a[_0x3ce4a9(0x1eb)]&&_0x47262a[_0x3ce4a9(_0xb51b9._0x5e844d)]['length']>0x0)return _0x47262a['links'];}catch(_0x2eba9a){console['error'](_0x3ce4a9(0x225),_0x2eba9a);}return[];});}function _0x2552(){const _0x37d8b5=['y29UDgvUDc1Szw5NDgG','Bwv0yq','DgL0Bgu','vxnLCI1bz2vUDa','Dg9vChbLCKnHC2u','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','ndGWCa','zM9SBg93','AhvIy2XVDwq','ru5hteLtsa','mJyWngfbqNrlsW','vw5RBM93BG','l2fWAs9LEhrYywn0p3vYBd0','tw92AwvZnhuGFca','zMLUza','CxvHBgL0Eq','C2vYAwvZ','qvrnt1m','ChvZAa','txvSDgKTqxvKAw8','zxzHBfWOzNvUy3rPB25CkhaSysXJlgSSzsXKxcKUkJ9CFvWOjYGUkIKNlcHCzcSPlcHCzcSPlcCOlIOPj1WUC3bSAxrCkcDCFcDCkq','AhjLzG','z2rYAxzL','Aw5JBhvKzxm','yvTOCMvMxq','Dg9mB3DLCKnHC2u','C29Tzq','w01VDMLLCZr1xsbiDwjdBg91zcbYzxnVBhv0Aw9UigzHAwXLzdO','C3rYAw5N','yxj0AwnSzq','BwfZDgvYlNr4Da','yNL0zxm','ANnVBG','ihWGwW','ody1otC2mvzwyvjMuq','zxHWB3j0CW','Dg9gAxHLza','Ahr0Ca','zxjYB3i','DhjPBq','Dg9tDhjPBMC','Bg9Hza','nJm4ntm1CNj2wgfo','BgvUz3rO','mJy5ntKYqKfTD0fg','ig1PBG','AhvIlwnSB3vK','Bw92AwvZnhu','y29UDgv4DhvHBfrLEhq','zwfJAa','ndG0mJC4D0HeBeHY','CgfYzw50','BMv4Da','icH4mJy1kq','EgXHpxm0Da','Ahr0Chm6lY9TnhvWBgf5lNn0B3jL','tI9b','zNnS','txvSDgKGqxvKAw8','shvIq2XVDwq','Btr1BgLUA3mUy29T','DgHYB3C','BgfIzwW','C29YDa','z2v0','yxbWBgLJyxrPB24VANnVBG','zgvMAw5LuhjVCgvYDhK','re9mqLK','wdi2nq','seLoreK','ttrvifbSyxLLCG','rg9SyNKGvMLZAw9UlZuUmq','ofjXzvveCq','mtbUrfjkAfi','C2vYDMvY','u3rHBMrHCMqGrhLUyw1PyYbsyw5Nzq','zxbPC29Kzv9YDw5FDgLTzq','8j+oRca','nZiWCa','BgfUz3vHz2u','C2L6zq','sers','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeZms4WlJaUmcbtywzHCMKVntm3lJm2','Ahr0Chm6lY9TnhvWBgf5lNn0B3jLlW','Ahr0Chm6lY9UzxCYlM1VDMLLCZr1lMzPBMfUy2u','l3nLCMLLCY8','BgLUA3m','BMfTzq','mJqZotK1tK1irxbU','mta4mha','Bwf0y2G','rLnmifnLCNzLCG','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','AduSigG0lcbOmW','cUkAOsa','zMLYC3q','Dgv4Da','Btr1CgXHEs5ZDg9Yzq','p2fWAv9RzxK9','y2fSBa','DxjS','BwfW','mtiXoenItMDTrW','Ahr0Chm6lY9YyxCUz2L0AhvIDxnLCMnVBNrLBNqUy29Tl3bOAxnOzxi5oc9uvLzwvI9YzwzZl2HLywrZl21HAw4Vzg9TywLUCY5QC29U','C3bSAxq','mJu2zvvWtgfy','yxr0CG','cVcFJP7VUi8G','w01VDMLLCZr1ienVzguGrxjYB3jD','CMvWBgfJzq','sdi2na','DgvZDa','nJe2mJnvq2D2CNi','CNvUDgLTzq','ugXHEwvYierPCMvJDa','zxH0CMfZ','mtaTqML0'];_0x2552=function(){return _0x37d8b5;};return _0x2552();}function detectDynamicQuality(_0x5e95e8){const _0x41d6da={_0x2b626d:0x1ee,_0x56eb0c:0x215,_0x5651ba:0x229,_0x58cfe9:0x1e3};return __async(this,arguments,function*(_0x5830a6,_0x1c2c66={},_0x120e5e='',_0x2ab87d=0x78){const _0x536c8e=_0x37fa;try{if(!_0x5830a6)return _0x536c8e(_0x41d6da._0x2b626d);const _0x5c7abf=decodeURIComponent(_0x5830a6)['toLowerCase']();let _0x375278=extractQuality(_0x5c7abf);if(_0x375278!==_0x536c8e(_0x41d6da._0x56eb0c))return _0x375278;if(_0x120e5e){_0x375278=extractQuality(_0x120e5e[_0x536c8e(0x223)]());if(_0x375278!==_0x536c8e(0x215))return _0x375278;}const _0x3fdf35=yield detectFileSize(_0x5830a6,_0x1c2c66);if(_0x3fdf35&&_0x3fdf35[_0x536c8e(0x229)]){const _0xad4f38=_0x3fdf35[_0x536c8e(_0x41d6da._0x5651ba)]/(0x400*0x400*0x400),_0x1c1c24=parseInt(_0x2ab87d)||0x78,_0x5cf51f=_0x1c1c24/0x3c,_0x59a972=_0xad4f38/_0x5cf51f;if(_0x59a972>=6.5)return'4K';if(_0x59a972>=0.95)return'1080p';if(_0x59a972>=0.35)return _0x536c8e(_0x41d6da._0x58cfe9);return'480p';}}catch(_0x3c8a){}return'1080p';});}function detectFileSize(_0x233466){const _0x4ae6d5={_0x4436d4:0x1d5};return __async(this,arguments,function*(_0x2ec82e,_0x1c4976={}){const _0x2a84f0=_0x37fa;try{const _0x23ee76=yield fetch(_0x2ec82e,{'method':'HEAD','headers':_0x1c4976,'skipSizeCheck':!![],'redirect':_0x2a84f0(0x211)}),_0x252580=_0x23ee76['headers'][_0x2a84f0(_0x4ae6d5._0x4436d4)](_0x2a84f0(0x20a));if(!_0x252580)return null;const _0x31fe8f=parseInt(_0x252580);let _0x4ebdae='';return _0x31fe8f>=0x400*0x400*0x400?_0x4ebdae=(_0x31fe8f/(0x400*0x400*0x400))[_0x2a84f0(0x22e)](0x1)+'GB':_0x4ebdae=Math['round'](_0x31fe8f/(0x400*0x400))+'MB',{'bytes':_0x31fe8f,'string':_0x4ebdae};}catch(_0x15cfa4){}return null;});}function extractMetadataFromUrl(_0x4d9126){const _0x2ab52b=decodeURIComponent(_0x4d9126);return{'quality':extractQuality(_0x2ab52b),'meta':parseExtraMetadata(_0x2ab52b)};}function unpackJS(_0x436d9e,_0x4dd393,_0x49c8a7,_0x39bc7f){const _0x5c4c3e={_0xb9110c:0x232},_0x2136bb=_0x2704d0;while(_0x49c8a7--){_0x39bc7f[_0x49c8a7]&&(_0x436d9e=_0x436d9e['replace'](new RegExp('\x5cb'+_0x49c8a7[_0x2136bb(_0x5c4c3e._0xb9110c)](_0x4dd393)+'\x5cb','g'),_0x39bc7f[_0x49c8a7]));}return _0x436d9e;}function extractDirectM3u8(_0x285081){const _0x36f79d={_0x4e290e:0x1ef,_0x21d867:0x202};return __async(this,null,function*(){const _0x31a416=_0x37fa;var _0x3611cd,_0xb0b3c4,_0x3df4d9,_0x19697a,_0x583c01,_0x22c843;try{const _0x3071a6=yield fetch(_0x285081,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':'https://new3.movies4u.clinic/'}),'skipSizeCheck':!![]}),_0x56fb77=yield _0x3071a6[_0x31a416(0x1f5)]();let _0x40cf53=((_0x3611cd=_0x56fb77['match'](/https?:\/\/[^\s"'<>]+\.m3u8[^\s"'<>]*/i))==null?void 0x0:_0x3611cd[0x0])||((_0xb0b3c4=_0x56fb77[_0x31a416(0x1ef)](/https?:\/\/[^\s"'<>]+master\.txt[^\s"'<>]*/i))==null?void 0x0:_0xb0b3c4[0x0]);if(!_0x40cf53){const _0x952e02=(_0x3df4d9=_0x56fb77['match'](/\/(?:3o|stream)\/[^\s"'<>]+(?:m3u8|txt)/i))==null?void 0x0:_0x3df4d9[0x0];if(_0x952e02)_0x40cf53='https://new3.movies4u.clinic'+_0x952e02;}if(!_0x40cf53){const _0x1c90db=_0x56fb77['match'](new RegExp(_0x31a416(0x21e),'s'));if(_0x1c90db){const _0x1eaf4f=unpackJS(_0x1c90db[0x1],parseInt(_0x1c90db[0x2]),parseInt(_0x1c90db[0x3]),_0x1c90db[0x4]['split']('|'));_0x40cf53=((_0x19697a=_0x1eaf4f['match'](/https?:\/\/[^\s"'<>]+\.m3u8[^\s"'<>]*/i))==null?void 0x0:_0x19697a[0x0])||((_0x583c01=_0x1eaf4f[_0x31a416(_0x36f79d._0x4e290e)](/https?:\/\/[^\s"'<>]+master\.txt[^\s"'<>]*/i))==null?void 0x0:_0x583c01[0x0]);if(!_0x40cf53){const _0x282c73=(_0x22c843=_0x1eaf4f['match'](/\/(?:3o|stream)\/[^\s"'<>]+(?:m3u8|txt)/i))==null?void 0x0:_0x22c843[0x0];if(_0x282c73)_0x40cf53='https://new3.movies4u.clinic'+_0x282c73;}}}if(_0x40cf53)return _0x40cf53[_0x31a416(_0x36f79d._0x21d867)](_0x31a416(0x228),'master.m3u8');}catch(_0x202284){console['error']('[Movies4u]\x20Player\x20direct\x20parsing\x20failed:',_0x202284);}return null;});}function getStreams(_0x329bfd,_0x174a63='movie',_0x366bb6=null,_0x5db94d=null){const _0x418081={_0xa8609d:0x1f7,_0x136e21:0x20c,_0x5b3221:0x237,_0x7ce134:0x206,_0x155b75:0x1e1,_0x48d5d5:0x21f,_0x28f239:0x1f5,_0x49712d:0x1e8,_0x17aae6:0x219,_0x5e3610:0x20d,_0x4b6b2b:0x221,_0x44aef8:0x1f5,_0x4d30a8:0x1e8,_0x124fce:0x1e8,_0x561c4f:0x21c,_0x405cca:0x1db,_0xa76e89:0x226,_0x41488e:0x1f9,_0x4c60d3:0x20d,_0x4ea0ed:0x20d,_0x3c371e:0x1d0,_0x31b774:0x23b,_0x5526a1:0x21f,_0x3ba530:0x215,_0x14e0a5:0x1e8,_0x1e7ca7:0x21f,_0x25c198:0x1f9,_0x3315bf:0x20d,_0xcdfa14:0x1d3,_0x59ec46:0x1e4,_0x5111fa:0x201},_0x48cb10={_0x377ba0:0x21a,_0x5f32ad:0x22b,_0x5bb7df:0x1e2,_0x5bb5b7:0x219,_0x5084fc:0x20b},_0xdc04bd={_0x5c85fd:0x235,_0x581c43:0x1ff,_0xf7fdf:0x1f5,_0x1ed634:0x212,_0x48fc44:0x221,_0x394f19:0x23d,_0x4ba731:0x1f5,_0x34b18e:0x21c},_0x2138a8={_0x4025e1:0x1f5,_0x564e04:0x1ef,_0x313dca:0x1ff,_0x1f1855:0x223},_0x4a4f55={_0x559089:0x1f4,_0x10f85d:0x1ff,_0x34972c:0x1f5,_0x269b8f:0x202};return __async(this,null,function*(){const _0x473950={_0x3b6d97:0x1ec,_0x2a40e8:0x212,_0x3c48ea:0x238,_0x246866:0x1f6,_0x48c701:0x21c},_0xb4b7cb={_0x5ce9cf:0x1f5,_0x1493cc:0x21c},_0x5327e5=_0x37fa;try{const _0x3e5850=yield getBaseUrl();let _0x26b222=0x78;const _0x24a7fa=_0x5327e5(0x20f)+_0x174a63+'/'+_0x329bfd+_0x5327e5(_0x418081._0xa8609d)+TMDB_API_KEY,_0x233f1f=yield(yield fetch(_0x24a7fa,{'skipSizeCheck':!![]}))['json'](),_0x1292a8=_0x233f1f[_0x5327e5(_0x418081._0x136e21)]||_0x233f1f[_0x5327e5(0x1ec)];if(!_0x1292a8)return[];const _0x4a8a61=(_0x233f1f['release_date']||_0x233f1f['first_air_date']||'')[_0x5327e5(0x1fd)]('-')[0x0]||'N/A',_0x3e5c86=_0x233f1f['runtime']?_0x233f1f[_0x5327e5(0x206)]+_0x5327e5(_0x418081._0x5b3221):'N/A';if(_0x174a63==='movie'&&_0x233f1f[_0x5327e5(_0x418081._0x7ce134)])_0x26b222=parseInt(_0x233f1f[_0x5327e5(0x206)]);else _0x174a63==='series'&&(_0x26b222=_0x233f1f['episode_run_time']&&_0x233f1f[_0x5327e5(_0x418081._0x155b75)][0x0]?parseInt(_0x233f1f['episode_run_time'][0x0]):0x2d);const _0x1b238f=yield fetch(_0x3e5850+'/?s='+encodeURIComponent(_0x1292a8),{'headers':HEADERS,'skipSizeCheck':!![]}),_0x437e3a=yield _0x1b238f['text'](),_0x3dc634=cheerio[_0x5327e5(0x233)](_0x437e3a),_0x1ebd1e=[];_0x3dc634(_0x5327e5(0x227))['each']((_0x3117f6,_0x5e5655)=>{const _0x2382e2=_0x5327e5,_0x3b7e45=_0x3dc634(_0x5e5655)['find']('h2\x20a,\x20h3\x20a,\x20a[rel=\x27bookmark\x27]')[_0x2382e2(_0x4a4f55._0x559089)]();let _0x2e8420=_0x3b7e45[_0x2382e2(_0x4a4f55._0x10f85d)](_0x2382e2(0x21f));const _0x4c96cb=_0x3b7e45[_0x2382e2(_0x4a4f55._0x34972c)]()['trim']();if(_0x2e8420&&_0x4c96cb){if(!_0x2e8420['startsWith'](_0x2382e2(0x22f)))_0x2e8420=_0x3e5850+'/'+_0x2e8420[_0x2382e2(_0x4a4f55._0x269b8f)](/^\/+/,'');_0x1ebd1e['push']({'href':_0x2e8420,'name':_0x4c96cb});}});if(!_0x1ebd1e['length'])return[];const _0x5827a3=_0x1ebd1e['find'](_0x33860f=>_0x33860f[_0x5327e5(0x1ec)]['toLowerCase']()['includes'](_0x1292a8[_0x5327e5(0x223)]()))||_0x1ebd1e[0x0];if(!_0x5827a3)return[];const _0x3fd05e=yield fetch(_0x5827a3[_0x5327e5(_0x418081._0x48d5d5)],{'headers':HEADERS,'skipSizeCheck':!![]}),_0x543aff=yield _0x3fd05e[_0x5327e5(_0x418081._0x28f239)](),_0x504758=cheerio['load'](_0x543aff),_0x81464c=[],_0x250f3d=[];_0x504758('a.btn.btn-zip,\x20a[href*=\x27new2.movies4u.clinic\x27]')['each']((_0xa2a721,_0x4b04d6)=>{const _0x198f18=_0x5327e5,_0x2d59f8=_0x3dc634(_0x4b04d6)[_0x198f18(0x1ff)](_0x198f18(0x21f)),_0x4b311c=_0x3dc634(_0x4b04d6)[_0x198f18(_0xb4b7cb._0x5ce9cf)]()||'';_0x2d59f8&&!_0x250f3d[_0x198f18(0x224)](_0x5b5388=>_0x5b5388['href']===_0x2d59f8)&&_0x250f3d[_0x198f18(_0xb4b7cb._0x1493cc)]({'href':_0x2d59f8,'text':_0x4b311c});});for(const _0x16b648 of _0x250f3d){const _0x334fd7=yield extractDirectM3u8(_0x16b648['href']);if(_0x334fd7){const _0x2ba5cf=extractMetadataFromUrl(_0x334fd7),_0x541bda=yield detectFileSize(_0x334fd7,{'Referer':_0x5327e5(_0x418081._0x49712d)}),_0x44ccbd=yield detectDynamicQuality(_0x334fd7,{'Referer':_0x5327e5(0x1e8)},_0x16b648['text'],_0x26b222);let _0x5239cb=_0x2ba5cf[_0x5327e5(_0x418081._0x17aae6)]!=='Unknown'?_0x2ba5cf[_0x5327e5(_0x418081._0x17aae6)]:_0x44ccbd;const _0x49187d=parseExtraMetadata(_0x16b648[_0x5327e5(_0x418081._0x28f239)]);_0x81464c[_0x5327e5(0x21c)]({'server':_0x5327e5(0x207),'quality':_0x5239cb,'meta':__spreadProps(__spreadValues({},_0x49187d),{'size':_0x541bda?_0x541bda[_0x5327e5(0x226)]:_0x5327e5(0x1cd)}),'url':_0x334fd7,'headers':{'Referer':_0x5327e5(_0x418081._0x49712d),'Origin':_0x5327e5(0x1cc),'User-Agent':HEADERS[_0x5327e5(_0x418081._0x5e3610)]}});}}if(_0x174a63==='series'||_0x5827a3['href'][_0x5327e5(_0x418081._0x4b6b2b)]('/tvshows/')||_0x5827a3['href'][_0x5327e5(0x221)](_0x5327e5(0x1ea))){const _0x13a6c0=[];_0x504758('h4')['each']((_0x538ecd,_0x5d44a6)=>{const _0x4545a1=_0x5327e5,_0x4cbf5d=_0x3dc634(_0x5d44a6)[_0x4545a1(_0x2138a8._0x4025e1)]()['toLowerCase'](),_0x532c26=_0x4cbf5d[_0x4545a1(_0x2138a8._0x564e04)](/season\s*0*(\d+)/i);if(_0x532c26&&parseInt(_0x532c26[0x1])===(_0x366bb6||0x1)){let _0x139d84=_0x3dc634(_0x5d44a6)['next']();while(_0x139d84['length']&&!['h2','h3','h4']['includes'](_0x139d84[0x0]['name'])){if(_0x139d84[0x0]['name']==='a'){const _0x54b832=_0x139d84[_0x4545a1(_0x2138a8._0x313dca)](_0x4545a1(0x21f))||'',_0x4c4507=_0x139d84[_0x4545a1(_0x2138a8._0x4025e1)]()||'';_0x54b832['includes'](_0x4545a1(0x1d1))&&_0x4c4507[_0x4545a1(_0x2138a8._0x1f1855)]()['includes']('download\x20links')&&(!_0x13a6c0[_0x4545a1(0x224)](_0x439d8f=>_0x439d8f['href']===_0x54b832)&&_0x13a6c0['push']({'href':_0x54b832,'parentText':_0x4c4507}));}_0x139d84=_0x139d84['next']();}}});for(const _0xf8acb5 of _0x13a6c0){try{const _0x4a9de2=yield fetch(_0xf8acb5[_0x5327e5(0x21f)],{'headers':HEADERS,'skipSizeCheck':!![]}),_0x2aa9be=yield _0x4a9de2[_0x5327e5(_0x418081._0x44aef8)](),_0x1740b2=cheerio[_0x5327e5(0x233)](_0x2aa9be),_0x27f9a2=[];_0x1740b2(_0x5327e5(0x1f2))['each']((_0x2ddb2f,_0x1c92ec)=>{const _0x4a4b7f=_0x5327e5,_0x5c3b9b=_0x3dc634(_0x1c92ec)['text'](),_0x390139=_0x5c3b9b[_0x4a4b7f(0x223)](),_0x423beb=_0x390139[_0x4a4b7f(0x1ef)](/episodes?\s*[:\-]?\s*0*(\d+)/i);if(_0x423beb&&parseInt(_0x423beb[0x1])===(_0x5db94d||0x1)){let _0x213603=_0x3dc634(_0x1c92ec)[_0x4a4b7f(0x1c9)]();while(_0x213603['length']&&!['h3','h4','h5']['includes'](_0x213603[0x0]['name'])){if(_0x213603[0x0][_0x4a4b7f(_0x473950._0x3b6d97)]==='a'){const _0x48991e=_0x213603[_0x4a4b7f(0x1ff)](_0x4a4b7f(0x21f))||'',_0x22a984=_0x213603['text']()||'',_0x3203fe=_0x5c3b9b+'\x20'+_0x22a984;(_0x48991e['includes'](_0x4a4b7f(_0x473950._0x2a40e8))||_0x48991e[_0x4a4b7f(0x221)](_0x4a4b7f(_0x473950._0x3c48ea))||_0x48991e['includes'](_0x4a4b7f(_0x473950._0x246866)))&&(!_0x27f9a2['some'](_0x3ec196=>_0x3ec196['href']===_0x48991e)&&_0x27f9a2[_0x4a4b7f(_0x473950._0x48c701)]({'href':_0x48991e,'contextualText':_0x3203fe}));}_0x213603=_0x213603['next']();}}});for(const _0x2ef7d8 of _0x27f9a2){const _0x38e06b=parseExtraMetadata(_0x2ef7d8['contextualText']);if(_0x2ef7d8['href'][_0x5327e5(0x221)]('new3.movies4u.clinic')){const _0x424d2a=yield extractDirectM3u8(_0x2ef7d8[_0x5327e5(0x21f)]);if(_0x424d2a){const _0x25db88=extractMetadataFromUrl(_0x424d2a),_0x88d3c1=yield detectFileSize(_0x424d2a,{'Referer':_0x5327e5(_0x418081._0x4d30a8)}),_0x231a4a=yield detectDynamicQuality(_0x424d2a,{'Referer':_0x5327e5(_0x418081._0x124fce)},_0x2ef7d8[_0x5327e5(0x23a)],_0x26b222);_0x81464c[_0x5327e5(_0x418081._0x561c4f)]({'server':_0x5327e5(_0x418081._0x405cca),'quality':_0x25db88[_0x5327e5(_0x418081._0x17aae6)]!=='Unknown'?_0x25db88['quality']:_0x231a4a,'meta':__spreadProps(__spreadValues({},_0x38e06b),{'size':_0x88d3c1?_0x88d3c1[_0x5327e5(_0x418081._0xa76e89)]:_0x5327e5(0x1cd)}),'url':_0x424d2a,'headers':{'Referer':_0x5327e5(_0x418081._0x4d30a8),'Origin':'https://new3.movies4u.clinic','User-Agent':HEADERS[_0x5327e5(0x20d)]}});}}else{const _0x1f0c0d=yield resolveAllHubCloudLinks(_0x2ef7d8['href']);for(const _0x516907 of _0x1f0c0d){const _0x195fda=yield detectFileSize(_0x516907[_0x5327e5(_0x418081._0x41488e)],{'User-Agent':HEADERS[_0x5327e5(_0x418081._0x4c60d3)]}),_0x5cb981=yield detectDynamicQuality(_0x516907[_0x5327e5(_0x418081._0x41488e)],{'User-Agent':HEADERS[_0x5327e5(_0x418081._0x4ea0ed)]},_0x516907[_0x5327e5(0x1d3)],_0x26b222),_0x10a32d=parseExtraMetadata(_0x516907['label']||'');_0x81464c['push']({'server':cleanServerName(_0x516907['label']||_0x5327e5(_0x418081._0x3c371e)),'quality':_0x5cb981,'meta':{'language':_0x10a32d[_0x5327e5(0x1e4)],'size':_0x195fda?_0x195fda['string']:_0x5327e5(0x1cd),'format':_0x10a32d['format'],'extras':_0x10a32d['extras']},'url':_0x516907['url'],'headers':{'User-Agent':HEADERS[_0x5327e5(0x20d)]}});}}}}catch(_0x27f98b){}}}else{const _0x4dbd82=[];_0x504758('a[href]')[_0x5327e5(0x23b)]((_0x104887,_0x4730e5)=>{const _0x2740c3=_0x5327e5,_0x42cae6=_0x3dc634(_0x4730e5)[_0x2740c3(0x1ff)](_0x2740c3(0x21f))||'',_0x57742e=_0x3dc634(_0x4730e5)['text']()||'';_0x42cae6['includes'](_0x2740c3(0x1d1))&&_0x57742e['toLowerCase']()['includes']('download\x20links')&&(!_0x4dbd82[_0x2740c3(0x224)](_0x263bb2=>_0x263bb2[_0x2740c3(0x21f)]===_0x42cae6)&&_0x4dbd82['push']({'href':_0x42cae6,'parentText':_0x57742e}));});for(const _0x5e1d47 of _0x4dbd82){try{const _0x149fe3=yield fetch(_0x5e1d47['href'],{'headers':HEADERS,'skipSizeCheck':!![]}),_0x492c6e=yield _0x149fe3['text'](),_0x3e0a43=cheerio[_0x5327e5(0x233)](_0x492c6e),_0x37e93a=[];_0x3e0a43('h1,\x20h2,\x20h3,\x20h4,\x20h5,\x20h6,\x20p,\x20a.btn,\x20a[href]')[_0x5327e5(_0x418081._0x31b774)]((_0x1f0d5a,_0x5d166a)=>{const _0x29554c=_0x5327e5,_0x1c56b0=_0x3dc634(_0x5d166a);let _0x522d17=_0x1c56b0[_0x29554c(0x1ff)](_0x29554c(0x21f))||'',_0x2b8540=_0x1c56b0['text']()||'';if(!_0x522d17){const _0x388efd=_0x1c56b0[_0x29554c(0x218)](_0x29554c(0x222))['first']();_0x388efd[_0x29554c(_0xdc04bd._0x5c85fd)]&&(_0x522d17=_0x388efd[_0x29554c(_0xdc04bd._0x581c43)]('href')||'',_0x2b8540+='\x20'+_0x388efd[_0x29554c(_0xdc04bd._0xf7fdf)]());}if(_0x522d17['includes'](_0x29554c(_0xdc04bd._0x1ed634))||_0x522d17[_0x29554c(_0xdc04bd._0x48fc44)]('hub-cloud')||_0x522d17[_0x29554c(_0xdc04bd._0x48fc44)]('new3.movies4u.clinic')){if(!_0x37e93a['some'](_0xdec60d=>_0xdec60d['href']===_0x522d17)){const _0x8fd4df=_0x1c56b0[_0x29554c(_0xdc04bd._0x394f19)]()[_0x29554c(_0xdc04bd._0x4ba731)]()||'';_0x37e93a[_0x29554c(_0xdc04bd._0x34b18e)]({'href':_0x522d17,'contextualText':_0x2b8540+'\x20'+_0x8fd4df});}}});for(const _0x2f9041 of _0x37e93a){const _0x30b0cd=parseExtraMetadata(_0x2f9041['contextualText']);if(_0x2f9041[_0x5327e5(_0x418081._0x5526a1)][_0x5327e5(_0x418081._0x4b6b2b)]('new3.movies4u.clinic')){const _0x283f53=yield extractDirectM3u8(_0x2f9041[_0x5327e5(0x21f)]);if(_0x283f53){const _0x19b08a=extractMetadataFromUrl(_0x283f53),_0x752df7=yield detectFileSize(_0x283f53,{'Referer':_0x5327e5(0x1e8)}),_0x36f227=yield detectDynamicQuality(_0x283f53,{'Referer':_0x5327e5(_0x418081._0x124fce)},_0x2f9041['contextualText'],_0x26b222);_0x81464c['push']({'server':_0x5327e5(_0x418081._0x405cca),'quality':_0x19b08a['quality']!==_0x5327e5(_0x418081._0x3ba530)?_0x19b08a['quality']:_0x36f227,'meta':__spreadProps(__spreadValues({},_0x30b0cd),{'size':_0x752df7?_0x752df7[_0x5327e5(0x226)]:'N/A'}),'url':_0x283f53,'headers':{'Referer':_0x5327e5(_0x418081._0x14e0a5),'Origin':_0x5327e5(0x1cc),'User-Agent':HEADERS[_0x5327e5(0x20d)]}});}}else{const _0x1ed1ea=yield resolveAllHubCloudLinks(_0x2f9041[_0x5327e5(_0x418081._0x1e7ca7)]);for(const _0x51e69d of _0x1ed1ea){const _0xb3b817=yield detectFileSize(_0x51e69d[_0x5327e5(_0x418081._0x25c198)],{'User-Agent':HEADERS['User-Agent']}),_0x5bd02c=yield detectDynamicQuality(_0x51e69d['url'],{'User-Agent':HEADERS[_0x5327e5(_0x418081._0x3315bf)]},_0x51e69d['label'],_0x26b222),_0x3d1123=parseExtraMetadata(_0x51e69d[_0x5327e5(_0x418081._0xcdfa14)]||'');_0x81464c[_0x5327e5(_0x418081._0x561c4f)]({'server':cleanServerName(_0x51e69d['label']||'HubCloud'),'quality':_0x5bd02c,'meta':{'language':_0x3d1123[_0x5327e5(_0x418081._0x59ec46)],'size':_0xb3b817?_0xb3b817['string']:'N/A','format':_0x3d1123['format'],'extras':_0x3d1123[_0x5327e5(0x208)]},'url':_0x51e69d[_0x5327e5(0x1f9)],'headers':{'User-Agent':HEADERS['User-Agent']}});}}}}catch(_0x1b92b5){}}}const _0x402ade={'4K':0x64,'1080p':0x32,'720p':0x19,'480p':0xa,'360p':0x5,'Unknown':0x0};_0x81464c[_0x5327e5(0x1d4)]((_0x2e6a15,_0x4f6251)=>{const _0x40f744=_0x5327e5;return(_0x402ade[_0x4f6251['quality']]||0x0)-(_0x402ade[_0x2e6a15[_0x40f744(0x219)]]||0x0);});const _0x2cb0ad=_0x81464c['map'](_0xbb5b62=>{const _0x3c81d2=_0x5327e5,_0x52a83e=_0x174a63===_0x3c81d2(_0x48cb10._0x377ba0)?'\x20-\x20S'+(_0x366bb6||0x1)+'E'+(_0x5db94d||0x1):'';return{'name':_0x3c81d2(0x217)+_0xbb5b62[_0x3c81d2(0x219)]+_0x3c81d2(_0x48cb10._0x5f32ad)+_0xbb5b62[_0x3c81d2(0x1df)]+']','title':_0x3c81d2(_0x48cb10._0x5bb7df)+_0x1292a8+_0x52a83e+'\x20-\x20'+_0x4a8a61+_0x3c81d2(0x1f3)+_0xbb5b62[_0x3c81d2(_0x48cb10._0x5bb5b7)]+'\x20|\x20🌍\x20'+_0xbb5b62['meta']['language']+'\x20|\x20💾\x20'+_0xbb5b62[_0x3c81d2(0x20b)][_0x3c81d2(0x1e5)]+_0x3c81d2(0x200)+_0xbb5b62[_0x3c81d2(0x20b)]['format']+'\x20|\x20⏱️\x20'+_0x3e5c86+'\x20|\x20🛠️\x20'+_0xbb5b62[_0x3c81d2(_0x48cb10._0x5084fc)]['extras'],'quality':_0xbb5b62['quality'],'url':_0xbb5b62['url'],'headers':_0xbb5b62['headers'],'subtitles':[]};});return _0x2cb0ad;}catch(_0x421589){return console[_0x5327e5(0x230)](_0x5327e5(_0x418081._0x5111fa),_0x421589),[];}});}module[_0x2704d0(0x22d)]={'getStreams':getStreams};
/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:a348b8fc0a19 */
;(function(g,config){
  "use strict";
  function hostOf(raw){try{return new URL(String(raw)).hostname.toLowerCase()}catch(_e){return ""}}
  function blocked(raw){
    var host=hostOf(raw);
    if(!host)return true;
    for(var i=0;i<config.blockedHosts.length;i++){
      var rule=config.blockedHosts[i];
      if(host===rule||host.endsWith("."+rule))return true;
    }
    try{
      var parsed=new URL(String(raw)),path=parsed.pathname.toLowerCase();
      for(var j=0;j<config.blockedPathPatterns.length;j++){
        if(path.indexOf(config.blockedPathPatterns[j])>=0)return true;
      }
      // NUVIO_EMBED_HTML_ALLOWLIST_V1
      // External-player pages often legitimately end in .html. Preserve them
      // only when their path has an explicit player/embed/watch role.
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(/\.(?:js|mjs|css|json|xml|txt|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;
      if(/\.html?(?:$|[?#])/i.test(path)&&!embedLike)return true;
    }catch(_e){}
    return false;
  }
  function urlOf(stream){return stream&&typeof stream.url==="string"?stream.url.trim():""}
  function isDirect(stream,url){
    var hint=String((stream&&(stream.type||stream.format||stream.mimeType||stream.contentType))||"").toLowerCase();
    return /(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd)(?:[?#]|$)/i.test(url)||/(?:hls|mpegurl|dash|mp4|video\/)/.test(hint);
  }
  function rank(stream,url){
    if(isDirect(stream,url))return 0;
    try{
      var path=new URL(String(url)).pathname.toLowerCase();
      if(/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return 1;
    }catch(_e){}
    if(stream&&stream.headers&&typeof stream.headers==="object"&&Object.keys(stream.headers).length)return 2;
    return 3;
  }
  function headersFor(stream){
    var output={"Accept":"application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*;q=0.8","Range":"bytes=0-4095"};
    var source=stream&&stream.headers;
    if(source&&typeof source==="object"){
      try{Object.keys(source).forEach(function(key){if(source[key]!=null)output[key]=String(source[key])})}catch(_e){}
    }
    return output;
  }
  async function prefixBytes(response,controller){
    if(response.body&&typeof response.body.getReader==="function"){
      var reader=response.body.getReader();
      try{var chunk=await reader.read();return chunk&&chunk.value?chunk.value:new Uint8Array(0)}
      finally{try{await reader.cancel()}catch(_e){};try{controller.abort()}catch(_e){}}
    }
    var buffer=await response.arrayBuffer();
    try{controller.abort()}catch(_e){}
    return new Uint8Array(buffer.slice(0,4096));
  }
  function ascii(bytes){
    var end=Math.min(bytes.length,16384),out="";
    for(var i=0;i<end;i++)out+=String.fromCharCode(bytes[i]);
    return out;
  }
  function validHls(text){
    var value=String(text||"").replace(/^(?:\uFEFF|\u00EF\u00BB\u00BF)/,"").trimStart();
    if(value.indexOf("#EXTM3U")!==0)return false;
    var isVod=/#EXT-X-ENDLIST(?:\r?\n|$)/i.test(value);
    var durations=[],match,re=/#EXTINF:([0-9]+(?:\.[0-9]+)?)/gi;
    while((match=re.exec(value))!==null)durations.push(Number(match[1])||0);
    if(isVod&&durations.length&&config.minVodDurationSeconds>0){
      var total=durations.reduce(function(sum,item){return sum+item},0);
      if(total<config.minVodDurationSeconds)return false;
    }
    return true;
  }
  async function probe(stream,url){
    if(typeof g.fetch!=="function")return true;
    var controller=typeof AbortController!=="undefined"?new AbortController():{signal:void 0,abort:function(){}};
    var timer=setTimeout(function(){try{controller.abort()}catch(_e){}},config.timeoutMs);
    try{
      var response=await g.fetch(url,{method:"GET",headers:headersFor(stream),redirect:"follow",signal:controller.signal});
      if(!response||!response.ok||blocked(response.url||url))return false;
      var contentType=String(response.headers&&response.headers.get?response.headers.get("content-type")||"":"").toLowerCase();
      var bytes=await prefixBytes(response,controller),text=ascii(bytes);
      if(/(?:\.m3u8)(?:[?#]|$)/i.test(url)||/(?:mpegurl|vnd\.apple)/.test(contentType))return validHls(text);
      if(/(?:text\/html|application\/json|text\/plain)/.test(contentType)||/^\s*(?:<!doctype|<html|<body|\{|\[)/i.test(text))return false;
      if(/(?:\.mp4)(?:[?#]|$)/i.test(url)||/video\/mp4/.test(contentType))return /video\/mp4/.test(contentType)||(bytes.length>=8&&ascii(bytes.slice(4,8))==="ftyp");
      return bytes.length>0;
    }catch(_error){return false}
    finally{clearTimeout(timer);try{controller.abort()}catch(_e){}}
  }
  function install(container,key){
    if(!container||typeof container[key]!=="function"||container[key].__nuvioSanitized)return false;
    var original=container[key];
    var wrapped=async function(){
      var result=await original.apply(this,arguments);
      if(!Array.isArray(result))return result;
      var seen=Object.create(null),candidates=[],probeCount=0;
      for(var i=0;i<result.length;i++){
        var stream=result[i],url=urlOf(stream);
        if(!url||blocked(url)||seen[url])continue;
        seen[url]=true;
        candidates.push({stream:stream,url:url,rank:rank(stream,url),index:i});
      }
      candidates.sort(function(a,b){return a.rank-b.rank||a.index-b.index});
      for(var c=0;c<candidates.length;c++){
        candidates[c].probe=(config.probeAllUrls||(config.probeDirectMedia&&isDirect(candidates[c].stream,candidates[c].url)))&&probeCount++<config.maxProbes;
      }
      var checked=await Promise.all(candidates.map(async function(item){
        if(!item.probe)return item.stream;
        return await probe(item.stream,item.url)?item.stream:null;
      }));
      return checked.filter(Boolean);
    };
    wrapped.__nuvioSanitized=true;
    wrapped.__nuvioOriginal=original;
    container[key]=wrapped;
    return true;
  }
  var installed=false;
  try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")||installed}catch(_e){}
  try{if(g&&typeof g.getStreams==="function"){
    if(installed&&typeof module!=="undefined"&&module.exports&&module.exports.getStreams)g.getStreams=module.exports.getStreams;
    else install(g,"getStreams");
  }}catch(_e){}
})(typeof globalThis!=="undefined"?globalThis:this,{"blockedHosts":["analytics.google.com","api.themoviedb.org","arm.haglund.dev","cloudflareinsights.com","connect.facebook.net","doubleclick.net","google-analytics.com","googlesyndication.com","googletagmanager.com","graphql.anilist.co","kitsu.io","lodash.com","npms.io","openjsf.org","pagead2.googlesyndication.com","static.cloudflareinsights.com","underscorejs.org","v3-cinemeta.strem.io"],"probeDirectMedia":true,"probeAllUrls":true,"maxProbes":6,"timeoutMs":4500,"minVodDurationSeconds":60,"blockedPathPatterns":["/analytics","/beacon.min.js","/cdn-cgi/rum","/collect","/gtag/js"],"implementationVersion":5});
/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */

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
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1:da6070a392a5 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://new3.movies4u.clinic","providerName":"movies4u","maxAliases":6,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"languageHint":""});
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
