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
})(typeof globalThis!=="undefined"?globalThis:this,[["cGxheWVyLnZpZGVhc3kubmV0","player.videasy.to"]]);
const _0xa7424a=_0x4a66;(function(_0x589b66,_0x59d20c){const _0x4878ef={_0x38b690:0x1f7,_0x4e863a:0x1ce,_0x30b9de:0x201,_0x455218:0x1e4,_0x59bb01:0x1c3,_0x4d4d1a:0x1f6},_0x301657=_0x4a66,_0x375cd2=_0x589b66();while(!![]){try{const _0x5c5cc4=parseInt(_0x301657(_0x4878ef._0x38b690))/0x1+-parseInt(_0x301657(_0x4878ef._0x4e863a))/0x2*(parseInt(_0x301657(_0x4878ef._0x30b9de))/0x3)+-parseInt(_0x301657(0x1ff))/0x4+-parseInt(_0x301657(0x1c0))/0x5*(-parseInt(_0x301657(0x20e))/0x6)+parseInt(_0x301657(0x212))/0x7+parseInt(_0x301657(0x21f))/0x8*(parseInt(_0x301657(_0x4878ef._0x455218))/0x9)+parseInt(_0x301657(_0x4878ef._0x59bb01))/0xa*(-parseInt(_0x301657(_0x4878ef._0x4d4d1a))/0xb);if(_0x5c5cc4===_0x59d20c)break;else _0x375cd2['push'](_0x375cd2['shift']());}catch(_0x21e459){_0x375cd2['push'](_0x375cd2['shift']());}}}(_0x429a,0x97807));var __async=(_0xd0c07d,_0x340765,_0x2fa615)=>{return new Promise((_0x5f3661,_0x15e11c)=>{const _0x119019=_0x4a66;var _0x24bf8e=_0x52b38a=>{const _0x267aa3=_0x4a66;try{_0x27eb35(_0x2fa615[_0x267aa3(0x1f5)](_0x52b38a));}catch(_0x275c10){_0x15e11c(_0x275c10);}},_0x3d784d=_0x436a1f=>{try{_0x27eb35(_0x2fa615['throw'](_0x436a1f));}catch(_0x5dca38){_0x15e11c(_0x5dca38);}},_0x27eb35=_0x516626=>_0x516626[_0x119019(0x1c5)]?_0x5f3661(_0x516626[_0x119019(0x1ed)]):Promise[_0x119019(0x1c1)](_0x516626[_0x119019(0x1ed)])[_0x119019(0x1c7)](_0x24bf8e,_0x3d784d);_0x27eb35((_0x2fa615=_0x2fa615['apply'](_0xd0c07d,_0x340765))[_0x119019(0x1f5)]());});},TMDB_API_KEY=_0xa7424a(0x213),TMDB_BASE_URL=_0xa7424a(0x211),WINGS_API_BASE=_0xa7424a(0x1c4),USER_AGENT=_0xa7424a(0x20d),REQUEST_HEADERS={'User-Agent':USER_AGENT,'Accept':_0xa7424a(0x1eb),'Origin':_0xa7424a(0x224),'Referer':_0xa7424a(0x220),'Cache-Control':'no-cache,\x20no-store,\x20must-revalidate','Pragma':'no-cache','Expires':'0'},SERVERS={'Hydrogen':{'path':_0xa7424a(0x223)},'Titanium':{'path':_0xa7424a(0x208)},'Oxygen':{'path':_0xa7424a(0x1ef)},'Lithium':{'path':'downloader2/sources-with-title'},'Krypton':{'path':_0xa7424a(0x1d9)},'Carbon':{'path':_0xa7424a(0x1f1)},'Aluminium':{'path':'lamovie/sources-with-title'},'Nitrogen':{'path':_0xa7424a(0x21b)},'Neon':{'path':'superflix/sources-with-title'},'Helium':{'path':_0xa7424a(0x1e1)}},jl=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174],Tf=[0x67452301,0xefcdab89,0x98badcfe,0x10325476],Js=0x3d,_f=0x8,ms=0x9e3779b9,Ys=[0x6d,0x76,0x6d,0x31],Sf=_0x37e181=>(_0x37e181*(_0x37e181+0x1)&0x1)===0x0,bf=_0x391c9f=>(_0x391c9f*(_0x391c9f+0x1)&0x1)===0x1;function ui(_0x55d008){const _0x59f141=_0xa7424a;return _0x55d008>>>=0x0,_0x55d008^=_0x55d008>>>0x10,_0x55d008=Math['imul'](_0x55d008,0x85ebca6b)>>>0x0,_0x55d008^=_0x55d008>>>0xd,_0x55d008=Math[_0x59f141(0x221)](_0x55d008,0xc2b2ae35)>>>0x0,_0x55d008^=_0x55d008>>>0x10,_0x55d008>>>0x0;}function ps(_0x347f79,_0x7edf3f){return _0x347f79>>>=0x0,_0x7edf3f&=0x1f,_0x7edf3f===0x0?_0x347f79>>>0x0:(_0x347f79<<_0x7edf3f|_0x347f79>>>0x20-_0x7edf3f)>>>0x0;}function If(_0x1f22c0){const _0x287fb3={_0x298dcc:0x221,_0x363fe6:0x1fe},_0x7e3be0=_0xa7424a;let _0xe6f21=Tf[0x0]>>>0x0;for(let _0x271667=0x0;_0x271667<_0x1f22c0['length'];_0x271667++){_0xe6f21=ps((_0xe6f21^Math[_0x7e3be0(_0x287fb3._0x298dcc)](_0x1f22c0[_0x7e3be0(_0x287fb3._0x363fe6)](_0x271667),jl[_0x271667&0xf]))>>>0x0,0x5);}return ui(_0xe6f21);}function Af(_0x343e78){const _0x1e8b40=_0xa7424a,_0x462795=new Array(0x100);for(let _0x2202f5=0x0;_0x2202f5<0x100;_0x2202f5++)_0x462795[_0x2202f5]=_0x2202f5;let _0x3654f8=0x0;for(let _0x1593a5=0x0;_0x1593a5<0x100;_0x1593a5++){_0x3654f8=_0x3654f8+_0x462795[_0x1593a5]+_0x343e78[_0x1e8b40(0x1fe)](_0x1593a5%_0x343e78[_0x1e8b40(0x1bf)])&0xff;const _0x393c75=_0x462795[_0x1593a5];_0x462795[_0x1593a5]=_0x462795[_0x3654f8],_0x462795[_0x3654f8]=_0x393c75;}return _0x462795;}function wf(_0x302fd9){const _0x3063e2={_0x324930:0x221},_0x58f133=_0xa7424a;let _0x37b6da=0x811c9dc5;for(let _0x4f989f=0x0;_0x4f989f<_0x302fd9['length'];_0x4f989f++){_0x37b6da=Math[_0x58f133(_0x3063e2._0x324930)](_0x37b6da^_0x302fd9['charCodeAt'](_0x4f989f),0x1000193)>>>0x0;}return ui(_0x37b6da);}function vf(_0xc8001c,_0x4b2aa1,_0x41cdd8){return((_0xc8001c^_0x4b2aa1)>>>0x0|(_0xc8001c&_0x4b2aa1&_0x41cdd8)>>>0x0)>>>0x0;}function Nf(_0x631558,_0x42b3cc){if(bf(_0x631558['length']))return{'S':Af(_0x631558),'acc':If(_0x631558)};const _0x2cbc01=new Array(Js);let _0x2bb9da=ui(wf(_0x631558)^ui(_0x42b3cc>>>0x0^ms))>>>0x0;for(let _0xfb5e8d=0x0;_0xfb5e8d<_f;_0xfb5e8d++){if(Sf(_0xfb5e8d)){const _0x1a78ae=_0x2bb9da%Js;_0x2bb9da=ps(_0x2bb9da+ms>>>0x0,0x7+(_0xfb5e8d&0x7)),_0x2cbc01[_0x1a78ae]=(_0x2bb9da^ui(_0x2bb9da))>>>0x0,_0x2bb9da=ui(_0x2bb9da+_0x1a78ae>>>0x0);}else _0x2cbc01[_0xfb5e8d]=jl[_0xfb5e8d&0xf];}return{'S':_0x2cbc01,'acc':ui(_0x2bb9da^0xa5a5a5a5)>>>0x0};}function Rf(_0xea83ed,_0x405e02){const _0xf4349d={_0x24af3b:0x203},_0x11d34e=_0xa7424a,_0x15d800=_0xea83ed['S'];let _0x4ac929=_0xea83ed[_0x11d34e(_0xf4349d._0x24af3b)];const _0x1a9656=_0x4ac929%Js,_0x188ab4=0x0-+(_0x1a9656 in _0x15d800),_0x1d77d1=_0x15d800[_0x1a9656]>>>0x0,_0x3b743f=Math['imul'](ms,_0x405e02+0x1)>>>0x0;let _0x57c0b2=vf(_0x4ac929,(_0x1d77d1^_0x3b743f)>>>0x0,_0x188ab4);return _0x57c0b2=(ps(_0x57c0b2+_0x4ac929>>>0x0,_0x1a9656&0x1f)^ps(_0x4ac929,Math['imul'](_0x1a9656,0x7)&0x1f))>>>0x0,_0x4ac929=ui(_0x57c0b2+ms>>>0x0),_0x15d800[_0x1a9656]=_0x4ac929>>>0x0,_0xea83ed['acc']=_0x4ac929,_0x4ac929>>>0x0;}function Cf(_0x121578,_0x2c5249,_0x17eb78){const _0x3ddc8a=Nf(_0x121578,_0x2c5249),_0x442b0e=new Uint8Array(_0x17eb78);let _0x396470=0x0;for(let _0x2f7e65=0x0;_0x2f7e65<_0x17eb78;){const _0x402e74=Rf(_0x3ddc8a,_0x396470++);_0x442b0e[_0x2f7e65++]=_0x402e74&0xff,_0x2f7e65<_0x17eb78&&(_0x442b0e[_0x2f7e65++]=_0x402e74>>>0x8&0xff),_0x2f7e65<_0x17eb78&&(_0x442b0e[_0x2f7e65++]=_0x402e74>>>0x10&0xff),_0x2f7e65<_0x17eb78&&(_0x442b0e[_0x2f7e65++]=_0x402e74>>>0x18&0xff);}return _0x442b0e;}function decodeBase64(_0x110a95){const _0x4e0652={_0x2dac4a:0x222,_0x51522a:0x227},_0x1233dc=_0xa7424a,_0x470eb7='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',_0x2666c3=_0x110a95[_0x1233dc(_0x4e0652._0x2dac4a)](/-/g,'+')[_0x1233dc(0x222)](/_/g,'/')[_0x1233dc(0x222)](/=+$/,''),_0x202116=_0x2666c3['length'],_0x2bfde0=new Uint8Array(Math['floor'](_0x202116*0.75));let _0x5ac383=0x0;for(let _0x38cd70=0x0;_0x38cd70<_0x202116;_0x38cd70+=0x4){const _0xce8190=_0x470eb7[_0x1233dc(0x227)](_0x2666c3[_0x38cd70]),_0x245cc4=_0x470eb7[_0x1233dc(_0x4e0652._0x51522a)](_0x2666c3[_0x38cd70+0x1]||'A'),_0x4163a0=_0x470eb7['indexOf'](_0x2666c3[_0x38cd70+0x2]||'A'),_0x33022f=_0x470eb7[_0x1233dc(0x227)](_0x2666c3[_0x38cd70+0x3]||'A');_0x2bfde0[_0x5ac383++]=_0xce8190<<0x2|_0x245cc4>>0x4;if(_0x38cd70+0x2<_0x202116)_0x2bfde0[_0x5ac383++]=(_0x245cc4&0xf)<<0x4|_0x4163a0>>0x2;if(_0x38cd70+0x3<_0x202116)_0x2bfde0[_0x5ac383++]=(_0x4163a0&0x3)<<0x6|_0x33022f;}return _0x2bfde0;}function xf(_0x158e23){return decodeBase64(_0x158e23);}function decryptWingsDatabase(_0x122b4d,_0x55054e,_0x55103e){const _0x5942c9={_0x5b2ddf:0x1bf,_0x3d5209:0x1e8},_0x48f50b=_0xa7424a,_0x450fdb=xf(_0x122b4d),_0x5ae58b=Cf(_0x55054e,_0x55103e,_0x450fdb['length']);for(let _0x29cd02=0x0;_0x29cd02<_0x450fdb[_0x48f50b(0x1bf)];_0x29cd02++)_0x450fdb[_0x29cd02]^=_0x5ae58b[_0x29cd02];for(let _0x2d4c0d=0x0;_0x2d4c0d<Ys[_0x48f50b(_0x5942c9._0x5b2ddf)];_0x2d4c0d++){if(_0x450fdb[_0x2d4c0d]!==Ys[_0x2d4c0d])throw new Error('decrypt\x20failed:\x20bad\x20seed\x20or\x20tampered\x20payload');}let _0x5eaced='';const _0x4ae975=_0x450fdb['subarray'](Ys['length']);for(let _0x339204=0x0;_0x339204<_0x4ae975['length'];){const _0x677c7e=_0x4ae975[_0x339204++];if(_0x677c7e<0x80)_0x5eaced+=String[_0x48f50b(_0x5942c9._0x3d5209)](_0x677c7e);else{if(_0x677c7e>0xbf&&_0x677c7e<0xe0)_0x5eaced+=String['fromCharCode']((_0x677c7e&0x1f)<<0x6|_0x4ae975[_0x339204++]&0x3f);else _0x677c7e>0xdf&&_0x677c7e<0xf0?_0x5eaced+=String['fromCharCode']((_0x677c7e&0xf)<<0xc|(_0x4ae975[_0x339204++]&0x3f)<<0x6|_0x4ae975[_0x339204++]&0x3f):_0x5eaced+=String['fromCharCode']((_0x677c7e&0x7)<<0x12|(_0x4ae975[_0x339204++]&0x3f)<<0xc|(_0x4ae975[_0x339204++]&0x3f)<<0x6|_0x4ae975[_0x339204++]&0x3f);}}return _0x5eaced;}function fetchMediaDetails(_0x5c8a2b,_0x4694a3,_0x3947bd,_0x42bb6e){const _0x4dd6a5={_0x5865a6:0x20f,_0x470cf7:0x222,_0x59c357:0x1c8,_0x2fb6e1:0x1f8,_0x372a14:0x206,_0x7fdfa2:0x1d8,_0x300906:0x1d7,_0x570a71:0x202,_0x2888fe:0x1e2};return __async(this,null,function*(){const _0x14b013=_0x4a66;var _0x2e90ea;let _0x821299=_0x4694a3==='tv'?_0x14b013(_0x4dd6a5._0x5865a6):'90\x20min';try{const _0x15806e=_0x4694a3==='tv'?'tv':'movie',_0x2b71a6=String(_0x5c8a2b)[_0x14b013(_0x4dd6a5._0x470cf7)](/\D/g,''),_0x5d776e=TMDB_BASE_URL+'/'+_0x15806e+'/'+_0x2b71a6+_0x14b013(_0x4dd6a5._0x59c357)+TMDB_API_KEY+_0x14b013(_0x4dd6a5._0x2fb6e1),_0x2fbf32=yield fetch(_0x5d776e,{'headers':{'User-Agent':REQUEST_HEADERS['User-Agent'],'Accept':_0x14b013(0x1fa)}});if(!_0x2fbf32['ok'])throw new Error(_0x14b013(_0x4dd6a5._0x372a14)+_0x2fbf32['status']);const _0x12de86=yield _0x2fbf32['json']();let _0x4cebc4=_0x821299;if(_0x4694a3===_0x14b013(0x1f9)&&_0x12de86['runtime'])_0x4cebc4=_0x12de86['runtime']+_0x14b013(0x21d);else{if(_0x4694a3==='tv'&&_0x3947bd!=null&&_0x42bb6e!=null){const _0x6695aa=TMDB_BASE_URL+'/tv/'+_0x2b71a6+_0x14b013(0x1f3)+_0x3947bd+'/episode/'+_0x42bb6e+'?api_key='+TMDB_API_KEY,_0x538a32=yield fetch(_0x6695aa);if(_0x538a32['ok']){const _0x4fbdb1=yield _0x538a32[_0x14b013(0x204)]();if(_0x4fbdb1&&_0x4fbdb1['runtime'])_0x4cebc4=_0x4fbdb1[_0x14b013(_0x4dd6a5._0x7fdfa2)]+_0x14b013(0x21d);else _0x12de86[_0x14b013(0x1d7)]&&_0x12de86[_0x14b013(_0x4dd6a5._0x300906)][_0x14b013(0x1bf)]>0x0&&(_0x4cebc4=_0x12de86['episode_run_time'][0x0]+'\x20min');}}}return{'title':_0x4694a3==='tv'?_0x12de86[_0x14b013(0x215)]:_0x12de86['title'],'year':(_0x4694a3==='tv'?_0x12de86['first_air_date']:_0x12de86[_0x14b013(_0x4dd6a5._0x570a71)]||'')[_0x14b013(_0x4dd6a5._0x2888fe)](0x0,0x4),'imdbId':((_0x2e90ea=_0x12de86['external_ids'])==null?void 0x0:_0x2e90ea['imdb_id'])||null,'mediaType':_0x4694a3,'duration':_0x4cebc4};}catch(_0xd5dfc6){return console['error']('[VidEasy]\x20TMDB\x20details\x20fetch\x20error:\x20'+_0xd5dfc6['message']),{'title':_0x4694a3==='tv'?_0x14b013(0x1d0):'Unknown\x20Movie','year':'N/A','imdbId':null,'mediaType':_0x4694a3,'duration':_0x821299};}});}function _0x4a66(_0x4f41e2,_0x418fb1){_0x4f41e2=_0x4f41e2-0x1be;const _0x429a76=_0x429a();let _0x4a6607=_0x429a76[_0x4f41e2];if(_0x4a66['TDSDIZ']===undefined){var _0x546b1b=function(_0x458c00){const _0x764488='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0xd0c07d='',_0x340765='';for(let _0x2fa615=0x0,_0x5f3661,_0x15e11c,_0x24bf8e=0x0;_0x15e11c=_0x458c00['charAt'](_0x24bf8e++);~_0x15e11c&&(_0x5f3661=_0x2fa615%0x4?_0x5f3661*0x40+_0x15e11c:_0x15e11c,_0x2fa615++%0x4)?_0xd0c07d+=String['fromCharCode'](0xff&_0x5f3661>>(-0x2*_0x2fa615&0x6)):0x0){_0x15e11c=_0x764488['indexOf'](_0x15e11c);}for(let _0x3d784d=0x0,_0x27eb35=_0xd0c07d['length'];_0x3d784d<_0x27eb35;_0x3d784d++){_0x340765+='%'+('00'+_0xd0c07d['charCodeAt'](_0x3d784d)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x340765);};_0x4a66['sGoAhR']=_0x546b1b,_0x4a66['YDcjRA']={},_0x4a66['TDSDIZ']=!![];}const _0x154d35=_0x429a76[0x0],_0xf0f180=_0x4f41e2+_0x154d35,_0x372f30=_0x4a66['YDcjRA'][_0xf0f180];return!_0x372f30?(_0x4a6607=_0x4a66['sGoAhR'](_0x4a6607),_0x4a66['YDcjRA'][_0xf0f180]=_0x4a6607):_0x4a6607=_0x372f30,_0x4a6607;}function getLangCode(_0x1c41f4){const _0x1035f1={_0x312150:0x1e9},_0x125771=_0xa7424a;if(!_0x1c41f4)return'en';const _0x4718de={'english':'en','spanish':'es','french':'fr','german':'de','italian':'it','portuguese':'pt','portuguese\x20(br)':'pt-br','arabic':'ar','japanese':'ja','korean':'ko','tamil':'ta','telugu':'te','malayalam':'ml','kannada':'kn','hindi':'hi','polish':'pl','greek':'el','croatian':'hr','ukrainian':'uk','lithuanian':'lt','thai':'th','estonian':'et','czech':'cs','zh-tw':_0x125771(0x1d2),'bokmål':'no','dutch':'nl','indonesian':'id','sinhala':'si','swedish':'sv','romanian':'ro','malay':'ms','persian':'fa','slovak':'sk','bulgarian':'bg','turkish':'tr','danish':'da','hebrew':'he','serbian':'sr','vietnamese':'vi','hungarian':'hu','icelandic':'is','albanian':'sq','bosnian':'bs','slovenian':'sl','bengali':'bn','macedonian':'mk'};return _0x4718de[_0x1c41f4[_0x125771(0x1e6)]()[_0x125771(_0x1035f1._0x312150)]()]||'en';}function formatStreamsForNuvio(_0x3fc9fd,_0x15041e,_0x35c64d,_0x515578,_0x1cd419){const _0x3a35d5={_0x26297e:0x1dc,_0x136f9b:0x1db},_0x11abbe={_0x4aad31:0x21a,_0x5219db:0x222,_0x466535:0x210,_0x4240ec:0x229,_0x16fab3:0x200,_0x21b3fe:0x1d4,_0x496661:0x1da,_0x1276cf:0x214,_0x2f48a6:0x219,_0x3fd1d6:0x1df,_0x2c58a6:0x209,_0xa8a3c:0x200,_0x1de014:0x207,_0x5bb290:0x200,_0x48b6a6:0x1ee,_0x1fe6da:0x216,_0x2a0df1:0x1fc,_0x1b73b4:0x1c6,_0x5a2ae2:0x1c2,_0x4afbe1:0x20b},_0x1a87a3=_0xa7424a;try{const _0x5abbc2=JSON['parse'](_0x3fc9fd);if(!_0x5abbc2||typeof _0x5abbc2!=='object')return[];const _0x32061f={'Referer':'https://www.vidking.net/','Origin':'https://www.vidking.net','User-Agent':USER_AGENT},_0x4282e5=(_0x5abbc2['subtitles']||[])[_0x1a87a3(0x1de)](_0x59e79b=>({'url':_0x59e79b['url'],'language':getLangCode(_0x59e79b['language']||_0x59e79b['lang']),'name':_0x59e79b[_0x1a87a3(0x1fd)]||_0x59e79b['lang']||'English','headers':_0x32061f})),_0x2a4d52={'Carbon':'💎','Helium':'🎈','Lithium':'🔋','Oxygen':'💨','Krypton':'🦸','Titanium':'🛡️','Hydrogen':'💧','Nitrogen':'🌿','Neon':'💡','Aluminium':'💿'},_0x18ccdd=_0x2a4d52[_0x15041e]||'🎬',_0x4273d5={'Hydrogen':'CDN','Titanium':_0x1a87a3(0x217),'Oxygen':'Neon2','Lithium':_0x1a87a3(0x205),'Krypton':'YM','Carbon':'MB-Flix','Aluminium':'LaMovie','Nitrogen':_0x1a87a3(0x1d3),'Neon':'SuperFlix','Helium':'1Movies'},_0x2840da=_0x4273d5[_0x15041e]||_0x15041e,_0x42db41=[];return(_0x5abbc2['sources']||[])['forEach'](_0x255fe5=>{const _0x5c4c28=_0x1a87a3;if(!_0x255fe5['url'])return;let _0x23cb3c=_0x255fe5[_0x5c4c28(_0x11abbe._0x4aad31)]||'1080p',_0x2ab764=_0x23cb3c[_0x5c4c28(_0x11abbe._0x5219db)](/\s*server\s*2\s*$/gi,'')['trim']();_0x15041e===_0x5c4c28(_0x11abbe._0x466535)&&(_0x2ab764=_0x5c4c28(0x1d5));let _0x102aff=_0x2ab764['toLowerCase'](),_0x4dd8b6='⚡\x20'+_0x2ab764;if(_0x102aff[_0x5c4c28(0x200)](_0x5c4c28(_0x11abbe._0x4240ec))||_0x102aff[_0x5c4c28(_0x11abbe._0x16fab3)]('4k'))_0x4dd8b6=_0x5c4c28(0x20a);else{if(_0x102aff[_0x5c4c28(0x200)]('1080'))_0x4dd8b6='🔥\x201080p';else{if(_0x102aff['includes']('720'))_0x4dd8b6=_0x5c4c28(_0x11abbe._0x21b3fe);else _0x102aff==='auto'&&(_0x4dd8b6=_0x5c4c28(_0x11abbe._0x496661));}}let _0x4c1264='Original\x20Audio',_0x16acb9=_0x5c4c28(0x1c9);if(_0x15041e===_0x5c4c28(_0x11abbe._0x1276cf)||_0x15041e==='Krypton')_0x4c1264='Original\x20Audio',_0x16acb9='🌍\x20Original\x20Audio';else{if(_0x15041e==='Oxygen')_0x4c1264=_0x5c4c28(0x1f4),_0x16acb9=_0x5c4c28(0x218);else{if(_0x15041e==='Aluminium')_0x4c1264='Dual-Audio',_0x16acb9=_0x5c4c28(_0x11abbe._0x2f48a6);else{if(_0x15041e===_0x5c4c28(_0x11abbe._0x3fd1d6)){const _0x5193be=(_0x255fe5[_0x5c4c28(_0x11abbe._0x2c58a6)]||'')['toLowerCase']();_0x5193be[_0x5c4c28(0x200)]('bengali')||_0x5193be[_0x5c4c28(_0x11abbe._0xa8a3c)](_0x5c4c28(_0x11abbe._0x1de014))?(_0x4c1264=_0x5c4c28(0x228),_0x16acb9='🇧🇩\x20Bengali'):(_0x4c1264='Normal\x20Hindi',_0x16acb9='🇮🇳\x20Hindi');}}}}const _0x47296f=_0x255fe5[_0x5c4c28(0x216)][_0x5c4c28(_0x11abbe._0x5bb290)](_0x5c4c28(_0x11abbe._0x48b6a6))?'M3U8':_0x255fe5[_0x5c4c28(_0x11abbe._0x1fe6da)][_0x5c4c28(0x200)]('.mp4')?'MP4':_0x5c4c28(_0x11abbe._0x2a0df1),_0x54570b=_0x35c64d[_0x5c4c28(0x209)]+(_0x35c64d['mediaType']==='tv'?'\x20S'+_0x515578+'E'+_0x1cd419:'');let _0x3f5fa9=_0x15041e;_0x3f5fa9==='Krypton'&&(_0x3f5fa9=_0x3f5fa9['replace'](/\s*(1080p\s+)?server\s*2\s*$/gi,'')[_0x5c4c28(0x1e9)]());const _0x196bb9=_0x5c4c28(_0x11abbe._0x1b73b4)+_0x54570b+_0x5c4c28(0x21c)+_0x35c64d['year']+')\x0a'+_0x4dd8b6+'\x20|\x20'+_0x16acb9+'\x20|\x20🎧\x20AAC\x0a🎞️\x20'+_0x47296f+'\x20|\x20⏱️\x20'+_0x35c64d[_0x5c4c28(_0x11abbe._0x5a2ae2)]+'\x0a'+_0x18ccdd+'\x20'+_0x3f5fa9+_0x5c4c28(0x1f0)+_0x2840da;_0x42db41['push']({'name':_0x5c4c28(_0x11abbe._0x4afbe1)+_0x2ab764+'\x20|\x20'+_0x4c1264,'title':_0x196bb9,'size':_0x196bb9,'description':_0x196bb9,'url':_0x255fe5[_0x5c4c28(_0x11abbe._0x1fe6da)],'quality':'','language':'','headers':_0x32061f,'subtitles':_0x4282e5,'provider':'videasy','_is4k':_0x102aff[_0x5c4c28(0x200)]('2160')||_0x102aff['includes']('4k'),'_serverName':_0x15041e});}),_0x42db41;}catch(_0x17e4e6){return console[_0x1a87a3(_0x3a35d5._0x26297e)]('[VidEasy]\x20Formatting\x20error:\x20'+_0x17e4e6[_0x1a87a3(_0x3a35d5._0x136f9b)]),[];}}function fetchFromWingsServer(_0x190fbc,_0x4fe0d1,_0x10593a,_0x53363a,_0xcee714,_0x5e2379,_0x120cb2,_0xc54b2e){const _0x51a429={_0x461d50:0x1cd,_0x350d8e:0x1e0,_0x30a9dc:0x20c,_0x652486:0x1cf};return __async(this,null,function*(){const _0x386b64=_0x4a66,_0x332b00={'title':_0xcee714['title'],'mediaType':_0x10593a,'year':String(_0xcee714['year']),'episodeId':String(_0xc54b2e||0x1),'seasonId':String(_0x120cb2||0x1),'tmdbId':String(_0x53363a),'imdbId':_0xcee714['imdbId']||'','enc':'2','seed':_0x5e2379},_0xa9ede1=Object[_0x386b64(_0x51a429._0x461d50)](_0x332b00)['map'](_0x4831c7=>encodeURIComponent(_0x4831c7)+'='+encodeURIComponent(_0x332b00[_0x4831c7]))[_0x386b64(0x1cc)]('&'),_0x1d9945=WINGS_API_BASE+'/'+_0x4fe0d1[_0x386b64(_0x51a429._0x350d8e)]+'?'+_0xa9ede1;console[_0x386b64(0x1d1)](_0x386b64(0x225)+_0x190fbc+':\x20'+_0x1d9945);try{const _0x147fb6=yield fetch(_0x1d9945,{'headers':REQUEST_HEADERS});if(!_0x147fb6['ok'])throw new Error('HTTP\x20'+_0x147fb6[_0x386b64(_0x51a429._0x30a9dc)]);const _0x1f1261=yield _0x147fb6[_0x386b64(0x1cb)]();if(!_0x1f1261||_0x1f1261[_0x386b64(0x1e9)]()==='')throw new Error(_0x386b64(_0x51a429._0x652486));const _0x355fcb=decryptWingsDatabase(_0x1f1261,_0x5e2379,Number(_0x53363a));if(!_0x355fcb)return[];const _0x3d8ccb=formatStreamsForNuvio(_0x355fcb,_0x190fbc,_0xcee714,_0x120cb2,_0xc54b2e);return console['log']('[VidEasy]\x20✅\x20Found\x20'+_0x3d8ccb['length']+'\x20stream(s)\x20from\x20'+_0x190fbc),_0x3d8ccb;}catch(_0x27e3ce){return console['warn']('[VidEasy]\x20❌\x20Error\x20from\x20'+_0x190fbc+':\x20'+_0x27e3ce['message']),[];}});}function _0x429a(){const _0x2337fd=['mw1VDMLLCY9ZB3vYy2vZlxDPDgGTDgL0Bgu','C3vIC3rYAw5N','zM9YrwfJAa','otK5mZK2r1v2EgX0','w1zPzevHC3LDifn0yxj0Aw5Nigv4DhjHy3rPB24GzM9YifrnreiGsuq6ia','Dg9mB3DLCKnHC2u','zxHWB3j0CW','zNjVBunOyxjdB2rL','DhjPBq','C29YDa','kI8Q','x3nLCNzLCK5HBwu','DMfSDwu','lM0ZDtG','BMvVBJiVC291CMnLCY13AxrOlxrPDgXL','ihWG8j+uLYbqCM92AwrLCJOG','BwiTzMXPEc9ZB3vYy2vZlxDPDgGTDgL0Bgu','w1zPzevHC3LDie1LzgLHierLDgfPBhm6ici','l3nLyxnVBI8','txvSDgKTqxvKAw8','BMv4Da','mJm0m3fotuvmtW','nJeWmJC1ruLHqKzi','jMfWCgvUzf90B19YzxnWB25Zzt1LEhrLCM5HBf9Pzhm','Bw92Awu','yxbWBgLJyxrPB24VANnVBG','x2LZngS','tuTw','BgfUz3vHz2u','y2HHCKnVzgvbDa','mJuYodi1mNHPsg9hwa','Aw5JBhvKzxm','mte3nZGZwvPfANfb','CMvSzwfZzv9KyxrL','ywnJ','ANnVBG','rg93BMXVywrLCJi','ve1eqIbivfrqia','yMfUz2XH','DgvQBY9ZB3vYy2vZlxDPDgGTDgL0Bgu','DgL0Bgu','8j+mNYaYmtyWCa','vMLKrwfZEsb8ia','C3rHDhvZ','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmI4WlJaUmcbtywzHCMKVntm3lJm2','ndCYmJaWwhrnEw5z','nduGBwLU','t3H5z2vU','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmW','mtu4mZy3m2vlr0TjqG','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','shLKCM9Nzw4','BMfTzq','DxjS','vgvQBW','8j+mJsbnDwX0As1bDwrPBW','8j+mJsbeDwfSluf1zgLV','CxvHBgL0Eq','Btr1AgqVC291CMnLCY13AxrOlxrPDgXL','ic0Gka','ig1PBG','iIaO','ogPLs25TDa','Ahr0Chm6lY93D3CUDMLKA2LUzY5UzxqV','Aw11Ba','CMvWBgfJzq','y2rUl3nVDxjJzxmTD2L0Ac10AxrSzq','Ahr0Chm6lY93D3CUDMLKA2LUzY5Uzxq','w1zPzevHC3LDiff1zxj5Aw5NihnLCNzLCIa','w1zPzevHC3LDifnLzwqGC3vJy2vZC2z1BgX5ihjLDhjPzxzLzdOG','Aw5KzxHpzG','qMvUz2fSAq','mJe2ma','w1zPzevHC3LDiezHAwXLzcb0BYbMzxrJAcbTzwrPysbKzxrHAwXZigzYB20Gve1eqI4','BgvUz3rO','ntblEg9eBM0','CMvZB2X2zq','zhvYyxrPB24','mtG5ndbdrKLkrgC','Ahr0Chm6lY9HCgKUC3bLzwrYywnLBgLNAhqUy29T','zg9Uzq','8j+oRca','DgHLBG','p2fWAv9RzxK9','8j+mJsbpCMLNAw5HBcbbDwrPBW','ChvZAa','Dgv4Da','AM9PBG','A2v5CW','ngTcyKvxCG','rw1WDhKGCMvZCg9UC2u','vw5RBM93BIbuvIbtAg93','Bg9N','EMGTDhC','ttrvseq','4PQHidCYmha','qxv0BW','w1zPzevHC3LDifrVDgfSihvUAxf1zsbZDhjLyw1ZigzVDw5KoIa','zxbPC29Kzv9YDw5FDgLTzq','CNvUDgLTzq','Ew0VC291CMnLCY13AxrOlxrPDgXL','4PQHief1Dg8','BwvZC2fNzq','zxjYB3i','EwvHCG','BwfW','twfNBMvZAxvT','Cgf0Aa'];_0x429a=function(){return _0x2337fd;};return _0x429a();}function getStreams(_0x4163e4,_0x4a8f82,_0x57a54f=null,_0x2338cf=null){const _0x2bfda2={_0x373f56:0x1dc,_0xb39988:0x1d1,_0x1a3da3:0x21e,_0x460243:0x1cd,_0x36c6d4:0x1ea,_0x5a6d02:0x1db},_0x4cb223={_0x403fa2:0x1fb,_0x2b2115:0x1ec,_0x3c7db6:0x227};return __async(this,null,function*(){const _0x48a053={_0x521a04:0x216,_0x48d69e:0x1ca},_0x29c729=_0x4a66;console[_0x29c729(0x1d1)](_0x29c729(0x1e5)+_0x4163e4+',\x20Type:\x20'+_0x4a8f82+(_0x4a8f82==='tv'?',\x20S:'+_0x57a54f+'E:'+_0x2338cf:''));try{const _0x3a5953=yield fetchMediaDetails(_0x4163e4,_0x4a8f82,_0x57a54f,_0x2338cf);if(!_0x3a5953)return console[_0x29c729(_0x2bfda2._0x373f56)](_0x29c729(0x1be)),[];console[_0x29c729(_0x2bfda2._0xb39988)](_0x29c729(0x1f2)+_0x3a5953['title']+_0x29c729(_0x2bfda2._0x1a3da3)+_0x3a5953[_0x29c729(0x1dd)]+')\x20|\x20Duration:\x20'+_0x3a5953[_0x29c729(0x1c2)]);const _0x17212a=WINGS_API_BASE+'/seed?mediaId='+_0x4163e4;console['log']('[VidEasy]\x20Fetching\x20seed\x20from:\x20'+_0x17212a);const _0x484d76=yield fetch(_0x17212a,{'headers':REQUEST_HEADERS});if(!_0x484d76['ok'])throw new Error('Seed\x20HTTP\x20'+_0x484d76['status']);const _0x4d5914=yield _0x484d76[_0x29c729(0x204)](),_0x4046c7=_0x4d5914['seed'];if(!_0x4046c7)throw new Error('No\x20seed\x20returned\x20from\x20API');console[_0x29c729(0x1d1)](_0x29c729(0x226)+_0x4046c7);const _0x62a48c=Object[_0x29c729(0x1cd)](SERVERS)['map'](_0x1a6008=>{const _0x174b87=SERVERS[_0x1a6008];return fetchFromWingsServer(_0x1a6008,_0x174b87,_0x4a8f82,_0x4163e4,_0x3a5953,_0x4046c7,_0x57a54f,_0x2338cf);}),_0x278a77=yield Promise['all'](_0x62a48c),_0x1f3c41=[];_0x278a77['forEach'](_0x9bb440=>{const _0x4860b5=_0x29c729;_0x1f3c41[_0x4860b5(0x1ca)](..._0x9bb440);});const _0x415d71=[],_0x2984c0=new Set();_0x1f3c41[_0x29c729(0x1e3)](_0x553aeb=>{const _0x25c223=_0x29c729;!_0x2984c0['has'](_0x553aeb[_0x25c223(_0x48a053._0x521a04)])&&(_0x2984c0['add'](_0x553aeb['url']),_0x415d71[_0x25c223(_0x48a053._0x48d69e)](_0x553aeb));});const _0x4daff2=Object[_0x29c729(_0x2bfda2._0x460243)](SERVERS);return _0x415d71[_0x29c729(_0x2bfda2._0x36c6d4)]((_0x5eece5,_0x1f4583)=>{const _0x46db9e=_0x29c729;if(_0x5eece5['_is4k']&&!_0x1f4583[_0x46db9e(_0x4cb223._0x403fa2)])return-0x1;if(!_0x5eece5['_is4k']&&_0x1f4583[_0x46db9e(0x1fb)])return 0x1;const _0x21bcd3=_0x4daff2[_0x46db9e(0x227)](_0x5eece5[_0x46db9e(_0x4cb223._0x2b2115)]),_0x55b90c=_0x4daff2[_0x46db9e(_0x4cb223._0x3c7db6)](_0x1f4583[_0x46db9e(0x1ec)]);return _0x21bcd3-_0x55b90c;}),console['log'](_0x29c729(0x1d6)+_0x415d71[_0x29c729(0x1bf)]),_0x415d71;}catch(_0x38985a){return console[_0x29c729(0x1dc)]('[VidEasy]\x20Error\x20in\x20getStreams:\x20'+_0x38985a[_0x29c729(_0x2bfda2._0x5a6d02)]),[];}});}module[_0xa7424a(0x1e7)]={'getStreams':getStreams};
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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:eced521e3481 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"videasy","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});



/* NUVIO_CATALOGUE_SCOPE_QUARANTINE_V1: provider=videasy */
;(function() {
  const __nuvioScopedRules = [{"kind":"fixture","fixture":"strict_movie_identity","mediaType":"movie","tmdbId":"1215638","reason":"playable_identity_contradiction"}];
  const __nuvioScopedProvider = "videasy";
  const __nuvioExports = (typeof module !== 'undefined' && module && module.exports) ? module.exports : null;
  const __nuvioOriginal = (__nuvioExports && typeof __nuvioExports.getStreams === 'function')
    ? __nuvioExports.getStreams
    : (typeof globalThis !== 'undefined' && typeof globalThis.getStreams === 'function' ? globalThis.getStreams : null);
  if (typeof __nuvioOriginal !== 'function') return;

  function __nuvioInvocation(args) {
    const first = args[0];
    if (first && typeof first === 'object' && !Array.isArray(first)) {
      return {
        tmdbId: String(first.tmdbId ?? first.id ?? ''),
        mediaType: String(first.mediaType ?? first.type ?? first.category ?? '').toLowerCase(),
        season: first.season == null ? null : Number(first.season),
        episode: first.episode == null ? null : Number(first.episode),
      };
    }
    return {
      tmdbId: String(first ?? ''),
      mediaType: String(args[1] ?? '').toLowerCase(),
      season: args[2] == null ? null : Number(args[2]),
      episode: args[3] == null ? null : Number(args[3]),
    };
  }

  function __nuvioMatches(rule, request) {
    if (String(rule.mediaType || '').toLowerCase() !== request.mediaType) return false;
    if (rule.kind === 'media_type') return true;
    if (String(rule.tmdbId || '') !== request.tmdbId) return false;
    if (rule.season != null && Number(rule.season) !== request.season) return false;
    if (rule.episode != null && Number(rule.episode) !== request.episode) return false;
    return true;
  }

  async function __nuvioScopedGetStreams(...args) {
    const request = __nuvioInvocation(args);
    if (__nuvioScopedRules.some((rule) => __nuvioMatches(rule, request))) return [];
    return await __nuvioOriginal.apply(this, args);
  }
  try { if (__nuvioExports && typeof __nuvioExports === 'object') __nuvioExports.getStreams = __nuvioScopedGetStreams; } catch {}
  try { if (typeof globalThis !== 'undefined') globalThis.getStreams = __nuvioScopedGetStreams; } catch {}
  try { if (typeof global !== 'undefined') global.getStreams = __nuvioScopedGetStreams; } catch {}
  try { if (typeof self !== 'undefined') self.getStreams = __nuvioScopedGetStreams; } catch {}
  try { if (typeof globalThis !== 'undefined') globalThis.__NUVIO_CATALOGUE_SCOPE_QUARANTINE__ = { provider: __nuvioScopedProvider, rules: __nuvioScopedRules }; } catch {}
})();

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
/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:262f37be8e53 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"videasy","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"cross-client-positive-mismatch-anime-confirmed-v3"});
/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:6bb5b5e3058d */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"videasy","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"all-providers-facts-badge-dedupe-tmdb-fallback-v9"});
