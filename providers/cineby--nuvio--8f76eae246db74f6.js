const _0x1c95ef=_0x16fc;(function(_0x1413cc,_0x5ddac4){const _0x457d1e={_0x133299:0xb2,_0x118acc:0xa6,_0x44e267:0x95,_0x15e5ca:0x9e,_0x441087:0x93,_0x408756:0x71,_0xdbdc97:0x6e},_0x1da568=_0x16fc,_0x26f66a=_0x1413cc();while(!![]){try{const _0x378b43=-parseInt(_0x1da568(_0x457d1e._0x133299))/0x1*(-parseInt(_0x1da568(_0x457d1e._0x118acc))/0x2)+parseInt(_0x1da568(_0x457d1e._0x44e267))/0x3*(parseInt(_0x1da568(0x96))/0x4)+parseInt(_0x1da568(0x99))/0x5*(-parseInt(_0x1da568(0x72))/0x6)+-parseInt(_0x1da568(_0x457d1e._0x15e5ca))/0x7*(parseInt(_0x1da568(0x78))/0x8)+-parseInt(_0x1da568(_0x457d1e._0x441087))/0x9+parseInt(_0x1da568(0xb0))/0xa+parseInt(_0x1da568(_0x457d1e._0x408756))/0xb*(parseInt(_0x1da568(_0x457d1e._0xdbdc97))/0xc);if(_0x378b43===_0x5ddac4)break;else _0x26f66a['push'](_0x26f66a['shift']());}catch(_0x4f020e){_0x26f66a['push'](_0x26f66a['shift']());}}}(_0x2157,0xec9d6));var __defProp=Object[_0x1c95ef(0x98)],__defProps=Object['defineProperties'],__getOwnPropDescs=Object[_0x1c95ef(0x6d)],__getOwnPropSymbols=Object[_0x1c95ef(0xb6)],__hasOwnProp=Object['prototype'][_0x1c95ef(0xaa)],__propIsEnum=Object['prototype'][_0x1c95ef(0x77)],__defNormalProp=(_0xe10ae9,_0x3ff632,_0x3ec53f)=>_0x3ff632 in _0xe10ae9?__defProp(_0xe10ae9,_0x3ff632,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x3ec53f}):_0xe10ae9[_0x3ff632]=_0x3ec53f,__spreadValues=(_0x119f85,_0x4b191f)=>{const _0x582889={_0x944e74:0x7b},_0x4e6c37=_0x1c95ef;for(var _0x5b5e38 in _0x4b191f||(_0x4b191f={}))if(__hasOwnProp['call'](_0x4b191f,_0x5b5e38))__defNormalProp(_0x119f85,_0x5b5e38,_0x4b191f[_0x5b5e38]);if(__getOwnPropSymbols)for(var _0x5b5e38 of __getOwnPropSymbols(_0x4b191f)){if(__propIsEnum[_0x4e6c37(_0x582889._0x944e74)](_0x4b191f,_0x5b5e38))__defNormalProp(_0x119f85,_0x5b5e38,_0x4b191f[_0x5b5e38]);}return _0x119f85;},__spreadProps=(_0x489483,_0x3766c8)=>__defProps(_0x489483,__getOwnPropDescs(_0x3766c8)),__async=(_0x2bbbbc,_0x27b479,_0x435e6f)=>{const _0x3b5e12={_0x441252:0x86},_0x1f124e={_0x35f4c8:0x86};return new Promise((_0x139466,_0x5a70a3)=>{const _0x46d254=_0x16fc;var _0x4c59f2=_0x2b7eb0=>{const _0x5b3657=_0x16fc;try{_0x3d7944(_0x435e6f[_0x5b3657(_0x1f124e._0x35f4c8)](_0x2b7eb0));}catch(_0x384c3b){_0x5a70a3(_0x384c3b);}},_0x4f2aed=_0xee2a8a=>{try{_0x3d7944(_0x435e6f['throw'](_0xee2a8a));}catch(_0xf26a55){_0x5a70a3(_0xf26a55);}},_0x3d7944=_0x4827a7=>_0x4827a7['done']?_0x139466(_0x4827a7[_0x46d254(0xb4)]):Promise['resolve'](_0x4827a7[_0x46d254(0xb4)])['then'](_0x4c59f2,_0x4f2aed);_0x3d7944((_0x435e6f=_0x435e6f['apply'](_0x2bbbbc,_0x27b479))[_0x46d254(_0x3b5e12._0x441252)]());});},DOMAINS_URL='https://raw.githubusercontent.com/sapariyaneel/nuvio-plugin/refs/heads/main/domains.json',FALLBACK_API_HOST=_0x1c95ef(0xad),TMDB_API_KEY='1865f43a0549ca50d341dd9ab8b29f49',HEADERS={'User-Agent':_0x1c95ef(0x9f),'Referer':'https://www.cineby.at/','Origin':'https://www.cineby.at'},cachedDomains=null;function getDomains(){return __async(this,null,function*(){if(cachedDomains)return cachedDomains;try{const _0x584599=yield fetch(DOMAINS_URL,{'skipSizeCheck':!![]});cachedDomains=yield _0x584599['json']();}catch(_0x37b489){cachedDomains={};}return cachedDomains;});}function getApiHost(){const _0x11524e={_0x4720c9:0x84};return __async(this,null,function*(){const _0x12d3d1=_0x16fc,_0x7e0ea9=yield getDomains();return(_0x7e0ea9['speedracelight']||_0x7e0ea9[_0x12d3d1(0xb9)]||FALLBACK_API_HOST)[_0x12d3d1(_0x11524e._0x4720c9)](/\/+$/,'');});}var SHA256_CONSTANTS=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174],MAGIC_BYTES=[0x6d,0x76,0x6d,0x31];function isCustomBranch(_0x21b2e6){return(_0x21b2e6*(_0x21b2e6+0x1)&0x1)===0x0;}function fmix32(_0x2d32ad){const _0x460932={_0x408387:0x7a},_0x411eda=_0x1c95ef;return _0x2d32ad=_0x2d32ad>>>0x0,_0x2d32ad^=_0x2d32ad>>>0x10,_0x2d32ad=Math[_0x411eda(_0x460932._0x408387)](_0x2d32ad,0x85ebca6b)>>>0x0,_0x2d32ad^=_0x2d32ad>>>0xd,_0x2d32ad=Math[_0x411eda(_0x460932._0x408387)](_0x2d32ad,0xc2b2ae35)>>>0x0,_0x2d32ad=(_0x2d32ad^_0x2d32ad>>>0x10)>>>0x0,_0x2d32ad;}function rotl32(_0x3968e5,_0x28915b){_0x3968e5=_0x3968e5>>>0x0,_0x28915b&=0x1f;if(_0x28915b===0x0)return _0x3968e5>>>0x0;return(_0x3968e5<<_0x28915b|_0x3968e5>>>0x20-_0x28915b)>>>0x0;}var BASE64_CHARS=_0x1c95ef(0x7f);function pureBase64Decode(_0x4a6253){const _0x588128={_0x5df4eb:0x88,_0x17f2c4:0x8d,_0x236c0:0xaf},_0x25fbe0=_0x1c95ef;let _0x3d9a9e='';for(let _0x26547f=0x0;_0x26547f<_0x4a6253[_0x25fbe0(0xaf)];_0x26547f++){const _0x2b39b5=_0x4a6253['charAt'](_0x26547f);if(_0x2b39b5!=='='&&BASE64_CHARS[_0x25fbe0(_0x588128._0x5df4eb)](_0x2b39b5)!==-0x1)_0x3d9a9e+=_0x2b39b5;}let _0x484e83='';for(let _0x50964b=0x0;_0x50964b<_0x3d9a9e[_0x25fbe0(0xaf)];_0x50964b+=0x4){const _0x2f56a2=BASE64_CHARS['indexOf'](_0x3d9a9e[_0x25fbe0(_0x588128._0x17f2c4)](_0x50964b)),_0x5e2513=BASE64_CHARS[_0x25fbe0(0x88)](_0x3d9a9e[_0x25fbe0(0x8d)](_0x50964b+0x1)),_0x45a55b=_0x50964b+0x2<_0x3d9a9e['length']?BASE64_CHARS[_0x25fbe0(_0x588128._0x5df4eb)](_0x3d9a9e[_0x25fbe0(0x8d)](_0x50964b+0x2)):-0x1,_0x416c65=_0x50964b+0x3<_0x3d9a9e[_0x25fbe0(_0x588128._0x236c0)]?BASE64_CHARS['indexOf'](_0x3d9a9e['charAt'](_0x50964b+0x3)):-0x1;_0x484e83+=String[_0x25fbe0(0xa3)](_0x2f56a2<<0x2|_0x5e2513>>0x4);if(_0x45a55b!==-0x1)_0x484e83+=String['fromCharCode']((_0x5e2513&0xf)<<0x4|_0x45a55b>>0x2);if(_0x416c65!==-0x1)_0x484e83+=String['fromCharCode']((_0x45a55b&0x3)<<0x6|_0x416c65);}return _0x484e83;}function _0x16fc(_0x3cfa36,_0x9b8e36){_0x3cfa36=_0x3cfa36-0x6d;const _0x215723=_0x2157();let _0x16fc13=_0x215723[_0x3cfa36];if(_0x16fc['iLDtSz']===undefined){var _0x23cf66=function(_0x2f5a30){const _0x237dfe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0xe10ae9='',_0x3ff632='';for(let _0x3ec53f=0x0,_0x119f85,_0x4b191f,_0x5b5e38=0x0;_0x4b191f=_0x2f5a30['charAt'](_0x5b5e38++);~_0x4b191f&&(_0x119f85=_0x3ec53f%0x4?_0x119f85*0x40+_0x4b191f:_0x4b191f,_0x3ec53f++%0x4)?_0xe10ae9+=String['fromCharCode'](0xff&_0x119f85>>(-0x2*_0x3ec53f&0x6)):0x0){_0x4b191f=_0x237dfe['indexOf'](_0x4b191f);}for(let _0x489483=0x0,_0x3766c8=_0xe10ae9['length'];_0x489483<_0x3766c8;_0x489483++){_0x3ff632+='%'+('00'+_0xe10ae9['charCodeAt'](_0x489483)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x3ff632);};_0x16fc['PbarLA']=_0x23cf66,_0x16fc['hZQBqO']={},_0x16fc['iLDtSz']=!![];}const _0xc1e5a6=_0x215723[0x0],_0x248518=_0x3cfa36+_0xc1e5a6,_0x5ce843=_0x16fc['hZQBqO'][_0x248518];return!_0x5ce843?(_0x16fc13=_0x16fc['PbarLA'](_0x16fc13),_0x16fc['hZQBqO'][_0x248518]=_0x16fc13):_0x16fc13=_0x5ce843,_0x16fc13;}function base64UrlToBytes(_0x27005d){const _0x38869b=_0x1c95ef,_0x41ab19=_0x27005d['replace'](/-/g,'+')[_0x38869b(0x84)](/_/g,'/')['padEnd'](0x4*Math['ceil'](_0x27005d['length']/0x4),'='),_0x34292b=typeof atob==='function'?atob(_0x41ab19):pureBase64Decode(_0x41ab19),_0x576466=new Uint8Array(_0x34292b['length']);for(let _0x3a848b=0x0;_0x3a848b<_0x34292b['length'];_0x3a848b++)_0x576466[_0x3a848b]=_0x34292b['charCodeAt'](_0x3a848b);return _0x576466;}function fnv1a32(_0x22dd18){const _0x3177c8={_0x59f7e1:0x7a,_0x2e9cd3:0x9b},_0x15303c=_0x1c95ef;let _0x248b4b=0x811c9dc5;for(let _0x177963=0x0;_0x177963<_0x22dd18['length'];_0x177963++)_0x248b4b=Math[_0x15303c(_0x3177c8._0x59f7e1)](_0x248b4b^_0x22dd18[_0x15303c(_0x3177c8._0x2e9cd3)](_0x177963),0x1000193)>>>0x0;return fmix32(_0x248b4b);}function makeKeystreamState(_0x2e4eab,_0x152fcc){const _0xd1a525=new Array(0x3d);let _0x3ec03f=fmix32(fnv1a32(_0x2e4eab)^fmix32(_0x152fcc>>>0x0^0x9e3779b9))>>>0x0;for(let _0x35d66c=0x0;_0x35d66c<0x8;_0x35d66c++){if(isCustomBranch(_0x35d66c)){const _0x6dd951=_0x3ec03f%0x3d;_0x3ec03f=rotl32(_0x3ec03f+0x9e3779b9>>>0x0,0x7+(0x7&_0x35d66c)),_0xd1a525[_0x6dd951]=(_0x3ec03f^fmix32(_0x3ec03f))>>>0x0,_0x3ec03f=fmix32(_0x3ec03f+_0x6dd951>>>0x0);}else _0xd1a525[_0x35d66c]=SHA256_CONSTANTS[0xf&_0x35d66c];}return{'slots':_0xd1a525,'acc':fmix32(0xa5a5a5a5^_0x3ec03f)>>>0x0};}function _0x2157(){const _0x5ff6c5=['nJG0odu5nvP3DuDhza','C3vIDgL0BgvZ','owz6C2jwBW','mteWodm0nezSsfnwvq','qNL0zxm','zgvMAw5LuhjVCgvYDhK','nujgruXXAa','C2vLza','y2HHCKnVzgvbDa','C3bSAxq','zxjYB3i','odeWnZa2neHuzxzQBq','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeZms4WlJaUmcbtywzHCMKVntm3lJm2','zxH0zxjUywXFAwrZ','BgfUz3vHz2u','vw5RBM93BG','zNjVBunOyxjdB2rL','zxHWB3j0CW','BMfTzq','nLjny1fjDW','Dgv4Da','zMXVB3i','jMv4DgvYBMfSx3nVDxjJzt1PBwrIx2LK','AgfZt3DUuhjVCgvYDhK','Dw5KzwzPBMvK','C291CMnLCW','Ahr0Chm6lY9HCgKUC3bLzwrYywnLBgLNAhqUy29T','q2LUzwj5ia','BgvUz3rO','mZG1mdi5mhjhtxHlva','BwfW','ntC2ntnyBhHOCNy','DgL0Bgu','DMfSDwu','l2nKBI9ZB3vYy2vZlxDPDgGTDgL0Bgu/','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ','zMLSDgvY','Bg9N','yxbPlNnWzwvKCMfJzwXPz2H0lMnVBq','Aw1KyL9Pza','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','ndG2mJrrA0XkENK','y29UDgvUDc1Yyw5Nzq','p2fWAv9RzxK9','ody0nMLyENL0za','mtaXmtuWmJjJDfHPu3q','Ahr0Ca','ANnVBG','Aw1KyKLK','y2vPBa','ChjVCgvYDhLjC0vUDw1LCMfIBgu','oeTmqKnyCq','ywnJ','Aw11Ba','y2fSBa','Bw92AwvFCMvZDwX0CW','w0nPBMvIEv0GzgvJCNLWDcbMywLSzwq6','CxvHBgL0Eq','qujdrevgr0HjsKTmtu5puffsu1rvvLDywvPHyMnKzwzNAgLQA2XTBM9WCxjZDhv2D3H5EJaXmJm0nty3odKRlW','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','yNL0zxm9mc0X','AxngAw5PDgu','y2f0y2G','CMvWBgfJzq','Bw92Awu','BMv4Da','DxjS','Aw5KzxHpzG','C2XPy2u','C3vIyxjYyxK','AgvHzgvYCW','DhzFCMvZDwX0CW','y2HHCKf0','Dg9gAxHLza','DhjPBq','ywXS','CMvSzwfZzv9KyxrL','Cg93'];_0x2157=function(){return _0x5ff6c5;};return _0x2157();}function nextKeystreamWord(_0x30ff07,_0x34583b){const _0x5824a6={_0x1ed574:0x7a},_0x58f89e=_0x1c95ef,_0x4f18be=_0x30ff07['slots'],_0x1028bb=_0x30ff07['acc'],_0x71bdc8=_0x1028bb%0x3d,_0x369161=_0x71bdc8 in _0x4f18be?-0x1:0x0,_0x4a9be7=_0x4f18be[_0x71bdc8]>>>0x0,_0x3bd0f4=(_0x4a9be7^Math['imul'](0x9e3779b9,_0x34583b+0x1)>>>0x0)>>>0x0,_0x7bdba=((_0x1028bb^_0x3bd0f4)>>>0x0|(_0x1028bb&_0x3bd0f4&_0x369161)>>>0x0)>>>0x0,_0x3d6292=(rotl32(_0x7bdba+_0x1028bb>>>0x0,0x1f&_0x71bdc8)^rotl32(_0x1028bb,0x1f&Math[_0x58f89e(_0x5824a6._0x1ed574)](_0x71bdc8,0x7)))>>>0x0,_0x57637b=fmix32(_0x3d6292+0x9e3779b9>>>0x0);return _0x4f18be[_0x71bdc8]=_0x57637b>>>0x0,_0x30ff07[_0x58f89e(0x79)]=_0x57637b,_0x57637b>>>0x0;}function generateKeystream(_0x28cfc2,_0x1fccb6,_0x604a16){const _0xa7122b=makeKeystreamState(_0x28cfc2,_0x1fccb6),_0x34d23a=new Uint8Array(_0x604a16);let _0xeb714b=0x0,_0x2ea9d6=0x0;while(_0xeb714b<_0x604a16){const _0x20593e=nextKeystreamWord(_0xa7122b,_0x2ea9d6++);_0x34d23a[_0xeb714b++]=0xff&_0x20593e;if(_0xeb714b<_0x604a16)_0x34d23a[_0xeb714b++]=_0x20593e>>>0x8&0xff;if(_0xeb714b<_0x604a16)_0x34d23a[_0xeb714b++]=_0x20593e>>>0x10&0xff;if(_0xeb714b<_0x604a16)_0x34d23a[_0xeb714b++]=_0x20593e>>>0x18&0xff;}return _0x34d23a;}function utf8BytesToString(_0x549940){const _0x147c74={_0x215f65:0xa3},_0x31c58b=_0x1c95ef;let _0x171c8a='',_0x25f76f=0x0;while(_0x25f76f<_0x549940['length']){const _0x340df2=_0x549940[_0x25f76f++];if(_0x340df2<0x80)_0x171c8a+=String['fromCharCode'](_0x340df2);else{if((_0x340df2&0xe0)===0xc0){const _0x290fb7=_0x549940[_0x25f76f++];_0x171c8a+=String['fromCharCode']((_0x340df2&0x1f)<<0x6|_0x290fb7&0x3f);}else{if((_0x340df2&0xf0)===0xe0){const _0x1bb43a=_0x549940[_0x25f76f++],_0x37c98c=_0x549940[_0x25f76f++];_0x171c8a+=String[_0x31c58b(_0x147c74._0x215f65)]((_0x340df2&0xf)<<0xc|(_0x1bb43a&0x3f)<<0x6|_0x37c98c&0x3f);}else{if((_0x340df2&0xf8)===0xf0){const _0x325db0=_0x549940[_0x25f76f++],_0x221911=_0x549940[_0x25f76f++],_0xaa76b0=_0x549940[_0x25f76f++];let _0x4566f=(_0x340df2&0x7)<<0x12|(_0x325db0&0x3f)<<0xc|(_0x221911&0x3f)<<0x6|_0xaa76b0&0x3f;_0x4566f-=0x10000,_0x171c8a+=String[_0x31c58b(0xa3)](0xd800+(_0x4566f>>0xa),0xdc00+(_0x4566f&0x3ff));}else _0x171c8a+=String[_0x31c58b(0xa3)](_0x340df2);}}}}return _0x171c8a;}function decryptSourcesPayload(_0x219443,_0x4d7883,_0x38593b){const _0x301527={_0x269e9e:0x8a},_0x59dd82=_0x1c95ef,_0x38f1b5=base64UrlToBytes(_0x219443),_0x542810=generateKeystream(_0x4d7883,_0x38593b,_0x38f1b5[_0x59dd82(0xaf)]),_0x23ed59=new Uint8Array(_0x38f1b5['length']);for(let _0x1b7189=0x0;_0x1b7189<_0x38f1b5[_0x59dd82(0xaf)];_0x1b7189++)_0x23ed59[_0x1b7189]=_0x38f1b5[_0x1b7189]^_0x542810[_0x1b7189];for(let _0x47945=0x0;_0x47945<MAGIC_BYTES[_0x59dd82(0xaf)];_0x47945++){if(_0x23ed59[_0x47945]!==MAGIC_BYTES[_0x47945])throw new Error('decrypt\x20failed:\x20bad\x20seed\x20or\x20tampered\x20payload');}const _0x592f55=_0x23ed59[_0x59dd82(_0x301527._0x269e9e)](MAGIC_BYTES['length']);return utf8BytesToString(_0x592f55);}function getTmdbMeta(_0x143a52,_0x45ac7d){const _0x5552a4={_0x2de402:0x85,_0x1b832d:0x74,_0x5414e9:0xa5,_0x28517b:0x91,_0x5d5fce:0xa0,_0x57011c:0xba};return __async(this,null,function*(){const _0x17f3b6=_0x16fc,_0x349966=_0x45ac7d==='tv'?'tv':_0x17f3b6(_0x5552a4._0x2de402),_0xc71d90=_0x17f3b6(0x80)+_0x349966+'/'+_0x143a52+_0x17f3b6(0x70)+TMDB_API_KEY+'&append_to_response=external_ids',_0x4fe2cf=yield fetch(_0xc71d90,{'skipSizeCheck':!![]});if(!_0x4fe2cf['ok'])return null;const _0x5b2511=yield _0x4fe2cf[_0x17f3b6(_0x5552a4._0x1b832d)](),_0x1ab70b=_0x349966==='tv'?_0x5b2511[_0x17f3b6(_0x5552a4._0x5414e9)]:_0x5b2511[_0x17f3b6(0xb3)],_0x57a10a=_0x349966==='tv'?_0x5b2511['first_air_date']:_0x5b2511[_0x17f3b6(_0x5552a4._0x28517b)],_0x2595b0=_0x57a10a?_0x57a10a[_0x17f3b6(0x89)](0x0,0x4):'',_0x2222b6=_0x5b2511[_0x17f3b6(_0x5552a4._0x5d5fce)]&&_0x5b2511[_0x17f3b6(0xa0)][_0x17f3b6(0xba)]||_0x5b2511[_0x17f3b6(_0x5552a4._0x57011c)]||'';return{'title':_0x1ab70b,'year':_0x2595b0,'imdbId':_0x2222b6};});}function qualityRank(_0x5a6344){const _0x58fb0d=_0x1c95ef;if(!_0x5a6344)return 0x0;if(/4k/i['test'](_0x5a6344))return 0x870;const _0x54ce0e=parseInt(_0x5a6344,0xa);return Number[_0x58fb0d(0x82)](_0x54ce0e)?_0x54ce0e:0x0;}function formatBytes(_0x360308){const _0x572abf={_0x38738e:0xa2,_0x23d493:0x97,_0x496641:0xb8,_0x1e5879:0x92,_0x595316:0x8e},_0x37895d=_0x1c95ef;if(!_0x360308)return _0x37895d(_0x572abf._0x38738e);const _0x242179=0x400,_0x1219fa=[_0x37895d(_0x572abf._0x23d493),'KB','MB','GB','TB'],_0x40f6c5=Math[_0x37895d(0xa8)](Math['log'](_0x360308)/Math[_0x37895d(_0x572abf._0x496641)](_0x242179));return parseFloat((_0x360308/Math[_0x37895d(_0x572abf._0x1e5879)](_0x242179,_0x40f6c5))[_0x37895d(_0x572abf._0x595316)](0x2))+'\x20'+_0x1219fa[_0x40f6c5];}var SEGMENT_SAMPLE_SIZE=0x5;function getRealSegmentSize(_0x18911a){const _0x14f173={_0x4ec36f:0x81,_0x48eaaf:0x8b};return __async(this,null,function*(){const _0x35daae=_0x16fc;try{const _0x2c7977=yield fetch(_0x18911a,{'method':'HEAD','headers':HEADERS,'skipSizeCheck':!![]}),_0x1612cc=_0x2c7977['headers']['get']('content-length');if(_0x1612cc)return parseInt(_0x1612cc,0xa);}catch(_0x1e4da8){}try{const _0x37b9c0=yield fetch(_0x18911a,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Range':_0x35daae(_0x14f173._0x4ec36f)}),'skipSizeCheck':!![]}),_0xb0d2fe=_0x37b9c0[_0x35daae(_0x14f173._0x48eaaf)]['get'](_0x35daae(0x6f)),_0x31f2e9=_0xb0d2fe&&_0xb0d2fe['match'](/\/(\d+)$/);if(_0x31f2e9)return parseInt(_0x31f2e9[0x1],0xa);}catch(_0x1b77af){}return null;});}function estimateHlsSize(_0x2f2291){const _0x4e3d71={_0x1287b0:0xa7,_0x32c60d:0x9c,_0xbca97d:0xb7,_0x16c00f:0x90,_0x3f8f25:0xaf};return __async(this,null,function*(){const _0x56f87b=_0x16fc;try{const _0x1c5bc=yield fetch(_0x2f2291,{'headers':HEADERS,'skipSizeCheck':!![]});if(!_0x1c5bc['ok'])return'Unknown';const _0x1f3282=yield _0x1c5bc[_0x56f87b(_0x4e3d71._0x1287b0)](),_0x30be14=_0x1f3282[_0x56f87b(_0x4e3d71._0x32c60d)]('\x0a')['map'](_0x53705d=>_0x53705d[_0x56f87b(0x8f)]())[_0x56f87b(_0x4e3d71._0xbca97d)](_0x355870=>_0x355870['startsWith'](_0x56f87b(0x73)));if(!_0x30be14[_0x56f87b(0xaf)])return'Unknown';const _0x538ed4=_0x30be14['filter']((_0x420f55,_0x1b41ec)=>_0x1b41ec%Math[_0x56f87b(0x76)](_0x30be14['length']/SEGMENT_SAMPLE_SIZE)===0x0)['slice'](0x0,SEGMENT_SAMPLE_SIZE),_0x46508a=yield Promise[_0x56f87b(_0x4e3d71._0x16c00f)](_0x538ed4[_0x56f87b(0xb1)](getRealSegmentSize)),_0x43a78c=_0x46508a[_0x56f87b(_0x4e3d71._0xbca97d)](_0x5bca19=>_0x5bca19&&_0x5bca19>0x0);if(!_0x43a78c[_0x56f87b(0xaf)])return _0x56f87b(0xa2);const _0x37be04=_0x43a78c['reduce']((_0x413c34,_0x5c108a)=>_0x413c34+_0x5c108a,0x0)/_0x43a78c[_0x56f87b(_0x4e3d71._0x3f8f25)],_0x4ce834=_0x37be04*_0x30be14['length'];return formatBytes(_0x4ce834);}catch(_0xc9f2e9){return'Unknown';}});}function getStreams(_0x1c38df,_0x4d3f49,_0x58af4c,_0x90d707){const _0x21a29f={_0x470497:0x8c,_0x1096c1:0x7c,_0x4613dd:0xaf,_0x2717cd:0xb3,_0x39d040:0x9a,_0x1f1fab:0xb5,_0x27dc89:0x9a,_0x47b779:0x9d,_0x248af3:0x7d,_0x4acd2f:0xac};return __async(this,null,function*(){const _0x49e9cc={_0x2d41d9:0x87,_0x2fa432:0x7e,_0x50aca0:0xa2},_0x31616e=_0x16fc;try{let _0x1353d6=_0x1c38df;if(typeof _0x1c38df==='string'&&_0x1c38df[_0x31616e(0x8f)]()['toLowerCase']()['startsWith']('tt')){const _0x2a50cd='https://api.themoviedb.org/3/find/'+_0x1c38df+_0x31616e(0x70)+TMDB_API_KEY+_0x31616e(0xa9),_0x79d92b=yield(yield fetch(_0x2a50cd,{'skipSizeCheck':!![]}))[_0x31616e(0x74)](),_0x5119a7=_0x4d3f49==='tv'?_0x79d92b[_0x31616e(_0x21a29f._0x470497)]:_0x79d92b[_0x31616e(_0x21a29f._0x1096c1)];_0x1353d6=_0x5119a7&&_0x5119a7[_0x31616e(_0x21a29f._0x4613dd)]?_0x5119a7[0x0]['id']:null;if(!_0x1353d6)return[];}_0x1353d6=parseInt(_0x1353d6,0xa);if(!_0x1353d6)return[];const _0x214874=yield getTmdbMeta(_0x1353d6,_0x4d3f49);if(!_0x214874||!_0x214874[_0x31616e(_0x21a29f._0x2717cd)])return[];const _0x1b29f5=yield getApiHost(),_0x355766=_0x4d3f49==='tv',_0x3599a6=yield fetch(_0x1b29f5+'/seed?mediaId='+_0x1353d6,{'headers':HEADERS,'skipSizeCheck':!![]});if(!_0x3599a6['ok'])return[];const _0x59b103=yield _0x3599a6['json']()[_0x31616e(0x83)](()=>null);if(!_0x59b103||!_0x59b103['seed'])return[];const _0x4f7d1b=new URLSearchParams({'title':_0x214874['title'],'mediaType':_0x355766?'tv':_0x31616e(0x85),'year':_0x214874['year']||'','episodeId':String(_0x355766?_0x90d707||0x1:0x1),'seasonId':String(_0x355766?_0x58af4c||0x1:0x1),'tmdbId':String(_0x1353d6),'imdbId':_0x214874[_0x31616e(0x75)]||'','enc':'2','seed':_0x59b103[_0x31616e(_0x21a29f._0x39d040)]}),_0x3b9cf6=yield fetch(_0x1b29f5+_0x31616e(_0x21a29f._0x1f1fab)+_0x4f7d1b['toString'](),{'headers':HEADERS,'skipSizeCheck':!![]});if(!_0x3b9cf6['ok'])return[];const _0x512e72=yield _0x3b9cf6['text']();let _0x1beafa;try{const _0x491ba3=decryptSourcesPayload(_0x512e72,_0x59b103[_0x31616e(_0x21a29f._0x27dc89)],_0x1353d6);_0x1beafa=JSON['parse'](_0x491ba3);}catch(_0x4214b0){return console[_0x31616e(_0x21a29f._0x47b779)](_0x31616e(_0x21a29f._0x248af3),_0x4214b0['message']),[];}const _0x103abf=_0x1beafa&&_0x1beafa[_0x31616e(_0x21a29f._0x4acd2f)]||[];if(!_0x103abf['length'])return[];const _0x3b1fdc=(_0x1beafa&&_0x1beafa[_0x31616e(0x94)]||[])[_0x31616e(0xb7)](_0x48c568=>_0x48c568&&_0x48c568['url'])['map'](_0x3cc3e6=>({'url':_0x3cc3e6['url'],'lang':_0x3cc3e6['lang']||_0x3cc3e6[_0x31616e(0xa1)]||_0x31616e(0xa2)})),_0x33247c=yield Promise[_0x31616e(0x90)](_0x103abf['filter'](_0x1785fe=>_0x1785fe&&_0x1785fe[_0x31616e(0x87)])['map'](_0x5c6fdd=>__async(this,null,function*(){const _0xae071d=_0x31616e,_0x5056fb=yield estimateHlsSize(_0x5c6fdd['url']);return{'url':_0x5c6fdd[_0xae071d(_0x49e9cc._0x2d41d9)],'quality':_0x5c6fdd['quality']||_0xae071d(0xa2),'title':_0xae071d(0xae)+(_0x5c6fdd[_0xae071d(_0x49e9cc._0x2fa432)]||_0xae071d(_0x49e9cc._0x50aca0)),'name':'Cineby','size':_0x5056fb,'headers':HEADERS,'subtitles':_0x3b1fdc};})));return _0x33247c['sort']((_0x5bb2b1,_0x3d14b6)=>qualityRank(_0x3d14b6[_0x31616e(0x7e)])-qualityRank(_0x5bb2b1['quality'])),_0x33247c;}catch(_0x485693){return console[_0x31616e(0x9d)]('[Cineby]',_0x485693),[];}});}typeof module!==_0x1c95ef(0xab)&&module['exports']?module[_0x1c95ef(0xa4)]={'getStreams':getStreams}:global['getStreams']=getStreams;
/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:a84149ed585b */
;(function(g,c){"use strict";
var ASSET=/\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|otf|eot|json|xml|vtt|srt)(?:[?#]|$)/i;
var BADHOST=/(?:^|\.)(?:youtube\.com|youtu\.be|twitter\.com|x\.com|twimg\.com|facebook\.com|instagram\.com|googletagmanager\.com|google-analytics\.com|doubleclick\.net)$/i;
var DEFAULT_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
function s(v){return String(v==null?"":v).replace(/\\\//g,"/").trim()}
function urlOf(row){var v=row&&row.url;if(v&&typeof v==="object")v=v.url||v.href||v.src;return s(v||(row&&(row.streamUrl||row.stream||row.link||row.file)))}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return""}}
function host(v){try{return new URL(v).hostname.toLowerCase()}catch(_){return""}}
function rejected(v){var h=host(v);return !/^https?:\/\//i.test(v)||!h||BADHOST.test(h)||ASSET.test(v)||/(?:trailer|bande-annonce|big[_-]?buck[_-]?bunny|sample[-_]?video|\/troll\/master\.m3u8)/i.test(v)}
function directByName(v){return /\.(?:m3u8|mpd|mp4|m4v|mkv|webm|ts)(?:[?#]|$)|\/hls2?\//i.test(v)}
function declaredDirect(row,v){var t=s(row&&(row.type||row.format||row.mimeType||row.contentType)).toLowerCase();return !!(row&&row.isDirect===true)||directByName(v)||/hls|mpegurl|m3u8|dash|mpd|mp4|m4v|matroska|mkv|webm|mpegts|mp2t|video\//i.test(t)}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function keyOf(o,name){var keys=Object.keys(o||{}),want=String(name||"").toLowerCase();for(var i=0;i<keys.length;i++)if(String(keys[i]).toLowerCase()===want)return keys[i];return""}
function setHeader(o,name,value){if(!value)return;var k=keyOf(o,name);if(k&&k!==name)delete o[k];o[name]=String(value)}
function responseHeader(r,name){try{return r&&r.headers&&typeof r.headers.get==="function"?s(r.headers.get(name)):""}catch(_e){return""}}
function baseHeaders(row){
  var out={};
  function merge(src){if(src&&typeof src==="object")Object.keys(src).forEach(function(k){if(String(k).toLowerCase()!=="range"&&s(src[k]))out[k]=s(src[k])})}
  try{merge(row&&row.url&&typeof row.url==="object"&&row.url.headers)}catch(_e){}
  try{merge(row&&row.headers)}catch(_e){}
  try{merge(row&&row.requestHeaders)}catch(_e){}
  try{merge(row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request)}catch(_e){}
  return out;
}
function normalizeRow(row){var u=urlOf(row);if(!u)return row;return Object.assign({},row,{url:u,headers:baseHeaders(row)})}
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
  if(c.defaultUserAgent&&!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",c.defaultUserAgent);
  var scoped=cookieHeader(jar,target),existing=keyOf(out,"Cookie");if(scoped)setHeader(out,"Cookie",mergeCookies(existing?out[existing]:"",scoped));
  if(!directByName(target)&&!keyOf(out,"Range"))out.Range="bytes=0-262143";
  return out;
}
function kindBytes(bytes){if(!bytes||bytes.length<4)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes[0]===71&&(bytes.length<189||bytes[188]===71))return"mpegts";return null}
function extensionKind(value){var m=s(value).toLowerCase().match(/\.(m3u8|mpd|mp4|m4v|mkv|webm|ts)(?:[?&#"'\s;]|$)/);if(!m)return null;return m[1]==="m3u8"?"hls":m[1]==="mpd"?"dash":m[1]==="m4v"?"mp4":m[1]==="ts"?"mpegts":m[1]}
function metadataKind(type,disposition,url){
  var ct=s(type).toLowerCase(),byName=extensionKind(s(disposition)+" "+s(url));
  if(/application\/(?:vnd\.apple\.mpegurl|x-mpegurl)|audio\/(?:mpegurl|x-mpegurl)/i.test(ct))return"hls";
  if(/application\/dash\+xml/i.test(ct))return"dash";
  if(/video\/(?:x-)?matroska|application\/(?:x-)?matroska/i.test(ct))return"mkv";
  if(/video\/(?:mp4|x-m4v|quicktime)/i.test(ct))return"mp4";
  if(/video\/webm/i.test(ct))return"webm";
  if(/video\/(?:mp2t|mpegts)/i.test(ct))return"mpegts";
  if(/^video\//i.test(ct))return byName||"video";
  if(/application\/(?:octet-stream|force-download)/i.test(ct)&&byName&&byName!=="hls"&&byName!=="dash")return byName;
  return byName&&byName!=="hls"&&byName!=="dash"?byName:null;
}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var x="";for(var i=0;i<Math.min(bytes.length,262144);i++)x+=String.fromCharCode(bytes[i]);return x}}
async function fetchResource(url,row,referer,jar){try{
  var requestHeaders=headers(row,referer,url,jar),r=await g.fetch(url,{headers:requestHeaders,redirect:"follow",signal:timeout()});if(!r)return null;
  var finalUrl=s(r.url||url);captureCookies(jar,r,finalUrl);
  var type=responseHeader(r,"content-type"),disposition=responseHeader(r,"content-disposition"),bytes=null,text="",meta=metadataKind(type,disposition,finalUrl);
  if(r.ok&&meta&&meta!=="hls"&&meta!=="dash")return{ok:true,status:r.status,url:finalUrl,type:type,disposition:disposition,bytes:null,text:"",metadataKind:meta,headers:headers(row,referer,finalUrl,jar)};
  if(typeof r.arrayBuffer==="function"){var buf=await r.arrayBuffer();bytes=new Uint8Array(buf);text=decode(bytes.slice(0,300000))}
  else if(typeof r.text==="function"){text=String(await r.text()||"").slice(0,300000)}
  return{ok:!!r.ok,status:r.status,url:finalUrl,type:type,disposition:disposition,bytes:bytes,text:text,metadataKind:meta,headers:headers(row,referer,finalUrl,jar)}
}catch(_){return null}}
function proof(r){if(!r||!r.ok)return null;var t=s(r.text).trimStart();if(t.indexOf("#EXTM3U")===0)return"hls";if(/<MPD[\s>]/i.test(t.slice(0,4096))||/application\/dash\+xml/i.test(r.type))return"dash";var b=kindBytes(r.bytes);if(b)return b;if(r.metadataKind)return r.metadataKind;if(/^video\//i.test(r.type)&&r.bytes&&r.bytes.length>12)return"video";return null}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;seen[u]=1;out.push(u)}var body=s(text),patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["'](https?:\/\/[^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mpd|mp4|m4v|mkv|webm|ts|embed|player|\/e\/|\/hls2?\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++){patterns[i].lastIndex=0;while((m=patterns[i].exec(body))!==null){add(m[1]);if(out.length>=c.maxCandidates)return out}}return out}
async function resolve(url,row,referer,depth,seen,jar){if(depth>c.maxDepth||rejected(url))return[];seen=seen||{};if(seen[url])return[];seen[url]=1;var r=await fetchResource(url,row,referer,jar);if(!r)return[];var k=proof(r);if(k)return[{url:r.url||url,kind:k,headers:r.headers}];if(!/html|text|json|javascript|xml/i.test(r.type)&&!/[<>{}\[\]"']/.test(r.text||""))return[];var next=candidates(r.text,r.url||url),out=[];for(var i=0;i<next.length&&out.length<c.maxCandidates;i++){var found=await resolve(next[i],row,r.url||url,depth+1,seen,jar);for(var j=0;j<found.length;j++)if(!out.some(function(x){return x.url===found[j].url}))out.push(found[j])}return out}
function slot(v){if(Array.isArray(v))return{key:null,list:v};if(v&&typeof v==="object"){for(var i=0;i<3;i++){var k=["streams","results","data"][i];if(Array.isArray(v[k]))return{key:k,list:v[k]}}}return null}
function rebuild(v,x,list){if(x.key===null)return list;var o=Object.assign({},v);o[x.key]=list;return o}
function clone(row,media){var out=Object.assign({},normalizeRow(row),{url:media.url,headers:media.headers||baseHeaders(row),isDirect:true,type:media.kind});if(media.kind==="hls"&&"format" in out)out.format="m3u8";if(media.kind==="dash"&&"format" in out)out.format="mpd";return out}
function refererOf(row,u){var h=baseHeaders(row),k=keyOf(h,"Referer");return s(k?h[k]:(row&&(row.referer||row.referrer||row.playerUrl||row.embedUrl||row.pageUrl))||u)}
async function enrich(list){var out=[],seen={};function add(row){row=normalizeRow(row);var u=urlOf(row);if(!u||seen[u])return;seen[u]=1;out.push(row)}for(var i=0;i<list.length;i++){var row=list[i];if(!row||typeof row!=="object")continue;var u=urlOf(row);if(!u||rejected(u))continue;if(declaredDirect(row,u)){add(row);continue}if(i<c.maxRows){var ref=refererOf(row,u),jar=[],found=await resolve(u,row,ref,0,{},jar);for(var j=0;j<found.length;j++)add(clone(row,found[j]));if(found.length)continue}/* Unresolved player/download pages are not playable streams. */}return out}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioGlobalMediaEnrichmentV1)return false;var native=o[k];var wrap=async function(){var v=await native.apply(this,arguments),x=slot(v);if(!x||!x.list.length)return v;var list=await enrich(x.list);return rebuild(v,x,list)};wrap.__nuvioGlobalMediaEnrichmentV1=true;o[k]=wrap;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true,"defaultUserAgent":"","implementationRevision":"scoped-playback-context-v6-direct-safe-opaque-media"});
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:6f1d134a7180 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"cineby","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
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
/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:dcc6c56d3a0c */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"cineby","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"cross-client-positive-mismatch-anime-confirmed-v3"});
/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:803cf246b5e4 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"cineby","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"all-providers-facts-badge-dedupe-tmdb-fallback-v9"});
