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
})(typeof globalThis!=="undefined"?globalThis:this,[["bmV3My5oZGh1YjR1LmNs","new4.hdhub4u.cl"]]);
function _0x1d41(){const _0x4db01a=['zw5J','n1nlz1L4BW','Cg9ZDf90AhvTyM5HAwW','mtK5nZj3s3fituK','Ahr0Chm6lY9UzxCXlMHKAhvInhuUy2W','DgL0Bgu','mtbqEM54yNi','y2HHCKf0','ChvZAa','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmW','Ahr0Chm6lY9YyxCUz2L0AhvIDxnLCMnVBNrLBNqUy29Tl3bOAxnOzxi5oc9uvLzwvI9YzwzZl2HLywrZl21HAw4Vzg9TywLUCY5QC29U','yM9KEq','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','p2LKpq','CJiUzgv2','zwfJAa','BwvZC2fNzq','zMLUza','zMLYC3rFywLYx2rHDgu','DxjS','CgL4zwXKCMe','w0HeshvInhvDifrnreiGsw5MBZOGiG','C3rHDhvZvgv4Da','qNL0zxm','mZC5oduXB1z0Bwvf','i2rVD25SB2fK','ieHIBgLUA3m','Dgv4Da','lNPPCa','ttnvoa','seriDwi0Dsa','w0HeshvInhvDiezLDgnOAw5Nihn0CMvHBxmGzM9YifrnreiGsuq6ia','jMfWCgvUzf90B19YzxnWB25Zzt1LEhrLCM5HBf9Pzhm','ywXS','vw5RBM93BG','qvzd','ChjVDg9JB2W','AduGysWGAdqGysWGAdmGyq','sgv4','CgvYBwfSAw5R','C3rHCNrZv2L0Aa','C3bSAxq','q0fn','AM9PBG','BM93','mtu2odaWmdDdugDQq3e','AgrZDhjLyw00Dq','v0vcuKLq','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9Y','C291CMnL','zMLSzu5HBwu','mZu3mJGZmgz6u1nLqG','Aw1KyL9Pza','Ahr0Chm6lY9ZzwfYy2GUCgLUz29Yys5MEwKVy29SBgvJDgLVBNmVCg9ZDc9KB2n1BwvUDhmVC2vHCMnOp3e9','BwfNBMv0oG','DMfSDwu','Ahr0Ca','EMLWzgLZAW','y3j5ChrVAw5ZAwDODhmUC2L0zq','z2v0','AgfZ','AgfZt3DUuhjVCgvYDhK','sdi2nq','BMv4Da','EwvHCG','w0HeshvInhvDiejLC3qGDgL0BguGBwf0y2G6ici','nZiWCa','iIaO','nJyWmdy0ogLmC0r3vG','p2rVD25SB2fK','lNbHz2uTyM9KEsa+igrPDIbH','u3rYzwfTvgfWzq','sfGTuMvKAxjLy3q','DhjPBq','BwfW','v0vclurm','re9mqLLwsvnjt04','wMLWrgLZAYbtzxj2zxi','shvIq2XVDwqGlsbgu0W','zMXHDa','AhvIy2XVDwqUy3G','w0HeshvInhvDiezHAwXLzcb0BYbMzxrJAcbSyxrLC3qGzg9TywLUCZOG','mdeYmZq1nJC4owfIy2rLzG','C3vIC3rYAw5N','y2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzL','DgHYB3C','BgLUAZ0','A2LLBxrPzw5TDwe5mtfJyq','qufd','Cg9ZDf90AxrSzq','shvIq2rU','ChjVCgvYDhLjC0vUDw1LCMfIBgu','BNvTyMvY','ywrK','zNjVBunOyxjdB2rL','ihrVia','serivui0Dq','CxvHBgL0Eq','q0jd','shvIq2XVDwqGlsaXmeDIChmG','CMvWBgfJzq','Dg9mB3DLCKnHC2u','EgXHpxm0Da','qujdrevgr0HjsKTmtu5puffsu1rvvLDywvPHyMnKzwzNAgLQA2XTBM9WCxjZDhv2D3H5EJaXmJm0nty3odKRlZ0','mtu4mda0nhn6yMLUra','x19LC01VzhvSzq','Bwf0y2G','AgL0CW','sgjmAw5RCW','Cg9W','l2rVD25SB2fK','CgfYC2u','zxbPC29Kzq','C29Tzq','Bg9N','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ','BgfZDeLUzgv4t2y','mJiZnJq1oeHyBwv5BW','zgvMAw5LuhjVCgvYDhK','CMvZB2X2zq','zNvUy3rPB24','C2v0','zgvMyxvSDa','rgLYzwn0ifiY','z2v0t3DUuhjVCgvYDhLoyw1LCW','ChjVDg90ExbL','uMvMzxjLCG','C3rHDhvZ','AhGTCMvKAxjLy3q','Aw5JBhvKzxm','AdeUCgfNzs10AxrSzsbZCgfU','CMv1CMW','AsnZAxPL','qLjssva','CZmGC2vYDMvY','w0HeshvInhvDifnLBgvJDgvKoIaI','y2fSBa','ifnLyxnVBIa','mta4mha','yMXVz191CMW','iIaOC2nVCMu6ia','AhvIy2XVDwqUAw5R','mtiZndu2nZG5mg9PDxL0CG','AhrTBa','C3rYAw5N','CMvSzwfZzv9KyxrL','C2L6zq','DgvJAhLIB3K0Dq','l2fWAs92ms92AwrLBZ9Pzd0','C2vHC29Uia','C3rYzwfTDgfWzs5JB20','zw51BwvYywjSzq','lcbuExbLoIa','yxr0CG','shvIq2XVDwq','BgvUz3rO','AhjLzG','vxrMoa','zgvMAw5LuhjVCgvYDgLLCW','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2','zNnSDJi','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','zNnSihnLCNzLCG','zxHWB3j0CW','Bw92Awu','AdmGysWGAdqGyq','zgf0yq','z2fKz2v0C3DLyI54ExO','tw96AwXSys81lJa','Dg9tDhjPBMC','ugL4zwXKCMfPBG','Ag9ZDg5HBwu','AhvIy2rU','AgrODwi0Dq','sdi2na','BwfUDwfS','Dg9vChbLCKnHC2u','rfrt','BMfTzq','zMLSDgvY','zxHLyW','wMLWrgLZAYbtzxj2zxiG','sgrtDhjLyw00Dq','Bg9Hza','B2jQzwn0','p2fWAv9RzxK9','r0vu','AgvHzgvYCW','neTsywD4ua','zxH0zxjUywXFAwrZ','Cg93','CgfKu3rHCNq','shvIC3rYzwfT','Bg9JyxrPB24','zMLUywXmAw5RCW'];_0x1d41=function(){return _0x4db01a;};return _0x1d41();}const _0x4cfe8c=_0x1850;(function(_0x4bd1e8,_0x326e94){const _0x3f3482={_0x2ebcc9:0xb1,_0x1082ec:0xe1,_0x1f3a99:0xaf,_0xdb40a:0xb4},_0x432f61=_0x1850,_0x252534=_0x4bd1e8();while(!![]){try{const _0x7c34e9=-parseInt(_0x432f61(_0x3f3482._0x2ebcc9))/0x1+-parseInt(_0x432f61(0x116))/0x2+parseInt(_0x432f61(0xc6))/0x3+parseInt(_0x432f61(0x16a))/0x4*(parseInt(_0x432f61(_0x3f3482._0x1082ec))/0x5)+-parseInt(_0x432f61(0x123))/0x6*(parseInt(_0x432f61(_0x3f3482._0x1f3a99))/0x7)+-parseInt(_0x432f61(0xf2))/0x8+parseInt(_0x432f61(0xdb))/0x9*(parseInt(_0x432f61(_0x3f3482._0xdb40a))/0xa);if(_0x7c34e9===_0x326e94)break;else _0x252534['push'](_0x252534['shift']());}catch(_0x3cc61a){_0x252534['push'](_0x252534['shift']());}}}(_0x1d41,0x8c864));var __create=Object['create'],__defProp=Object[_0x4cfe8c(0x124)],__defProps=Object[_0x4cfe8c(0x14c)],__getOwnPropDesc=Object[_0x4cfe8c(0xde)],__getOwnPropDescs=Object[_0x4cfe8c(0x14f)],__getOwnPropNames=Object[_0x4cfe8c(0x12a)],__getOwnPropSymbols=Object[_0x4cfe8c(0x121)],__getProtoOf=Object['getPrototypeOf'],__hasOwnProp=Object['prototype'][_0x4cfe8c(0xeb)],__propIsEnum=Object[_0x4cfe8c(0x12b)][_0x4cfe8c(0x109)],__defNormalProp=(_0x88bbc8,_0x59e2f6,_0x38ec05)=>_0x59e2f6 in _0x88bbc8?__defProp(_0x88bbc8,_0x59e2f6,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x38ec05}):_0x88bbc8[_0x59e2f6]=_0x38ec05,__spreadValues=(_0x586ac9,_0x243eff)=>{const _0x3d2fc4=_0x4cfe8c;for(var _0x4d4ed6 in _0x243eff||(_0x243eff={}))if(__hasOwnProp['call'](_0x243eff,_0x4d4ed6))__defNormalProp(_0x586ac9,_0x4d4ed6,_0x243eff[_0x4d4ed6]);if(__getOwnPropSymbols)for(var _0x4d4ed6 of __getOwnPropSymbols(_0x243eff)){if(__propIsEnum[_0x3d2fc4(0x136)](_0x243eff,_0x4d4ed6))__defNormalProp(_0x586ac9,_0x4d4ed6,_0x243eff[_0x4d4ed6]);}return _0x586ac9;},__spreadProps=(_0x2528ff,_0x869b1a)=>__defProps(_0x2528ff,__getOwnPropDescs(_0x869b1a)),__copyProps=(_0x5d58d3,_0x472071,_0x7c0d03,_0xd1c451)=>{const _0x1dddaa={_0x1e108d:0x126,_0x4dbc4a:0x145},_0x4d34db=_0x4cfe8c;if(_0x472071&&typeof _0x472071===_0x4d34db(0x166)||typeof _0x472071===_0x4d34db(_0x1dddaa._0x1e108d)){for(let _0x32d39b of __getOwnPropNames(_0x472071))if(!__hasOwnProp[_0x4d34db(0x136)](_0x5d58d3,_0x32d39b)&&_0x32d39b!==_0x7c0d03)__defProp(_0x5d58d3,_0x32d39b,{'get':()=>_0x472071[_0x32d39b],'enumerable':!(_0xd1c451=__getOwnPropDesc(_0x472071,_0x32d39b))||_0xd1c451[_0x4d34db(_0x1dddaa._0x4dbc4a)]});}return _0x5d58d3;},__toESM=(_0x522601,_0x375c55,_0x1820cc)=>(_0x1820cc=_0x522601!=null?__create(__getProtoOf(_0x522601)):{},__copyProps(_0x375c55||!_0x522601||!_0x522601[_0x4cfe8c(0x117)]?__defProp(_0x1820cc,'default',{'value':_0x522601,'enumerable':!![]}):_0x1820cc,_0x522601)),__async=(_0x1389ca,_0x1ef12d,_0x2af041)=>{return new Promise((_0x217d5a,_0x5e2a10)=>{const _0x928a11={_0x2c1548:0x103},_0x3664ae=_0x1850;var _0x1c6bd1=_0x464de7=>{const _0x1eac05=_0x1850;try{_0x2518b0(_0x2af041[_0x1eac05(0xed)](_0x464de7));}catch(_0x4da465){_0x5e2a10(_0x4da465);}},_0xd2a47f=_0x185354=>{const _0x536ed0=_0x1850;try{_0x2518b0(_0x2af041[_0x536ed0(_0x928a11._0x2c1548)](_0x185354));}catch(_0x325b10){_0x5e2a10(_0x325b10);}},_0x2518b0=_0x3b9469=>_0x3b9469['done']?_0x217d5a(_0x3b9469[_0x3664ae(0xe5)]):Promise[_0x3664ae(0x125)](_0x3b9469['value'])['then'](_0x1c6bd1,_0xd2a47f);_0x2518b0((_0x2af041=_0x2af041['apply'](_0x1389ca,_0x1ef12d))['next']());});},import_cheerio_without_node_native2=__toESM(require('cheerio-without-node-native')),TMDB_API_KEY=_0x4cfe8c(0xba),TMDB_BASE_URL=_0x4cfe8c(0xb7),MAIN_URL=_0x4cfe8c(0xb2),DOMAINS_URL=_0x4cfe8c(0xb8),DOMAIN_CACHE_TTL=0x4*0x3c*0x3c*0x3e8,HEADERS={'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/131.0.0.0\x20Safari/537.36\x20Edg/131.0.0.0','Cookie':_0x4cfe8c(0x114),'Referer':MAIN_URL+'/'};function updateMainUrl(_0x2bc9ad){const _0x633fe5=_0x4cfe8c;MAIN_URL=_0x2bc9ad,HEADERS[_0x633fe5(0x12c)]=_0x2bc9ad+'/';}var domainCacheTimestamp=0x0;function formatBytes(_0x3c872b){const _0x3b4efe={_0x5bc7d1:0xc5,_0x1039cb:0xa9},_0x84971e=_0x4cfe8c;if(!_0x3c872b||_0x3c872b===0x0)return _0x84971e(0xd0);const _0x58bc76=0x400,_0x4e1b4d=[_0x84971e(_0x3b4efe._0x5bc7d1),'KB','MB','GB','TB'],_0x15c2ec=Math['floor'](Math['log'](_0x3c872b)/Math['log'](_0x58bc76));return parseFloat((_0x3c872b/Math[_0x84971e(_0x3b4efe._0x1039cb)](_0x58bc76,_0x15c2ec))['toFixed'](0x1))+'\x20'+_0x4e1b4d[_0x15c2ec];}function extractServerName(_0x308c00){const _0x188b6f={_0x316e2a:0xd6,_0x3266c4:0x108,_0x4f30b0:0x11a,_0x2e18fb:0xab,_0x32d545:0xd7},_0xf06425=_0x4cfe8c;if(!_0x308c00)return'Unknown';if(_0x308c00[_0xf06425(0xd6)]('HubCloud')){const _0x36e3ab=_0x308c00['match'](/HubCloud(?:\s*-\s*([^[\]]+))?/);return _0x36e3ab?_0x36e3ab[0x1]||'Download':'HubCloud';}if(_0x308c00['startsWith']('Pixeldrain'))return'Pixeldrain';if(_0x308c00[_0xf06425(0xd6)]('StreamTape'))return _0xf06425(0xf5);if(_0x308c00[_0xf06425(_0x188b6f._0x316e2a)](_0xf06425(_0x188b6f._0x3266c4)))return _0xf06425(0x108);if(_0x308c00[_0xf06425(0xd6)](_0xf06425(_0x188b6f._0x4f30b0)))return _0xf06425(_0x188b6f._0x4f30b0);if(_0x308c00['startsWith'](_0xf06425(0xab)))return _0xf06425(_0x188b6f._0x2e18fb);return _0x308c00['replace'](/^www\./,'')[_0xf06425(_0x188b6f._0x32d545)]('.')[0x0];}function rot13(_0x457d9a){const _0x8001ce={_0x55e8e0:0x112},_0x2cd556=_0x4cfe8c;return _0x457d9a[_0x2cd556(_0x8001ce._0x55e8e0)](/[a-zA-Z]/g,function(_0x359643){const _0x3d42fb=_0x2cd556;return String[_0x3d42fb(0x10c)]((_0x359643<='Z'?0x5a:0x7a)>=(_0x359643=_0x359643['charCodeAt'](0x0)+0xd)?_0x359643:_0x359643-0x1a);});}var BASE64_CHARS=_0x4cfe8c(0x115);function atob(_0x5adf3b){const _0x36b0d1={_0x3d0b0c:0xb5},_0x4be03e=_0x4cfe8c;if(!_0x5adf3b)return'';let _0x54ae01=String(_0x5adf3b)['replace'](/=+$/,''),_0x26a2bf='',_0x3af0cf=0x0,_0x4c155d,_0x23c38e,_0x23662f=0x0;while(_0x23c38e=_0x54ae01[_0x4be03e(_0x36b0d1._0x3d0b0c)](_0x23662f++)){_0x23c38e=BASE64_CHARS['indexOf'](_0x23c38e),~_0x23c38e&&(_0x4c155d=_0x3af0cf%0x4?_0x4c155d*0x40+_0x23c38e:_0x23c38e,_0x3af0cf++%0x4&&(_0x26a2bf+=String['fromCharCode'](0xff&_0x4c155d>>(-0x2*_0x3af0cf&0x6))));}return _0x26a2bf;}function cleanTitle(_0x297d1f){const _0x78f195={_0x298a74:0xf9,_0x38b158:0x112,_0x28f38f:0xec,_0x3d84f:0x15c,_0x25fea9:0xdd,_0x33b0d2:0x133,_0x3160f9:0xd1},_0x4d4d4a={_0x37a267:0x15e,_0x1540dc:0x11f,_0x987da1:0xfa},_0x2b47ef=_0x4cfe8c;let _0x5d2ab8=_0x297d1f['replace'](/\.[a-zA-Z0-9]{2,4}$/,'');const _0x41af30=_0x5d2ab8['replace'](/WEB[-_. ]?DL/gi,_0x2b47ef(_0x78f195._0x298a74))[_0x2b47ef(_0x78f195._0x38b158)](/WEB[-_. ]?RIP/gi,'WEBRIP')['replace'](/H[ .]?265/gi,_0x2b47ef(_0x78f195._0x28f38f))[_0x2b47ef(_0x78f195._0x38b158)](/H[ .]?264/gi,_0x2b47ef(_0x78f195._0x3d84f))[_0x2b47ef(0x112)](/DDP[ .]?([0-9]\.[0-9])/gi,'DDP$1'),_0x23ddbd=_0x41af30[_0x2b47ef(0xd7)](/[\s_.]/),_0x4c9494=new Set(['WEB-DL',_0x2b47ef(_0x78f195._0x25fea9),'BLURAY','HDRIP','DVDRIP','HDTV',_0x2b47ef(0xd8),'TS',_0x2b47ef(_0x78f195._0x33b0d2),'BDRIP']),_0x41a9cf=new Set(['H264','H265','X264','X265','HEVC',_0x2b47ef(_0x78f195._0x3160f9)]),_0x13d603=[_0x2b47ef(0x106),'AC3',_0x2b47ef(0x15f),'MP3','FLAC','DD','DDP','EAC3'],_0x44d8f7=new Set(['ATMOS']),_0x4b10ed=new Set(['SDR','HDR','HDR10','HDR10+','DV','DOLBYVISION']),_0x522135=_0x23ddbd['map'](_0x58df58=>{const _0x12c8ab=_0x2b47ef,_0xe390ee=_0x58df58[_0x12c8ab(_0x4d4d4a._0x37a267)]();if(_0x4c9494['has'](_0xe390ee))return _0xe390ee;if(_0x41a9cf['has'](_0xe390ee))return _0xe390ee;if(_0x13d603[_0x12c8ab(_0x4d4d4a._0x1540dc)](_0x1a4762=>_0xe390ee[_0x12c8ab(0xd6)](_0x1a4762)))return _0xe390ee;if(_0x44d8f7[_0x12c8ab(0xea)](_0xe390ee))return _0xe390ee;if(_0x4b10ed['has'](_0xe390ee))return _0xe390ee==='DOLBYVISION'||_0xe390ee==='DV'?_0x12c8ab(_0x4d4d4a._0x987da1):_0xe390ee;if(_0xe390ee==='NF'||_0xe390ee==='CR')return _0xe390ee;return null;})[_0x2b47ef(0x161)](Boolean);return[...new Set(_0x522135)][_0x2b47ef(0xd9)]('\x20');}function fetchAndUpdateDomain(){const _0x1937ef={_0x3401ab:0x14d};return __async(this,null,function*(){const _0x14b1d5=_0x1850,_0x36af68=Date[_0x14b1d5(0xda)]();if(_0x36af68-domainCacheTimestamp<DOMAIN_CACHE_TTL)return;console['log']('[HDHub4u]\x20Fetching\x20latest\x20domain...');try{const _0x277b12=yield fetch(DOMAINS_URL,{'method':_0x14b1d5(0x168),'headers':{'User-Agent':_0x14b1d5(_0x1937ef._0x3401ab)}});if(_0x277b12['ok']){const _0x34efb6=yield _0x277b12['json']();if(_0x34efb6&&_0x34efb6[_0x14b1d5(0x10e)]){const _0x5f1f97=_0x34efb6[_0x14b1d5(0x10e)];_0x5f1f97!==MAIN_URL&&(console['log']('[HDHub4u]\x20Updating\x20domain\x20from\x20'+MAIN_URL+_0x14b1d5(0x10d)+_0x5f1f97),updateMainUrl(_0x5f1f97),domainCacheTimestamp=_0x36af68);}}}catch(_0xbe2ec5){console['error'](_0x14b1d5(0xff)+_0xbe2ec5[_0x14b1d5(0xbe)]);}});}function getCurrentDomain(){return __async(this,null,function*(){return yield fetchAndUpdateDomain(),MAIN_URL;});}function normalizeTitle(_0x4ff874){const _0x5bcbe8={_0x4c9ca8:0x113,_0x5f0c34:0x112,_0x18539b:0x112,_0xe6898a:0x112,_0x26937b:0xf7},_0x6d1b1a=_0x4cfe8c;if(!_0x4ff874)return'';return _0x4ff874[_0x6d1b1a(_0x5bcbe8._0x4c9ca8)]()[_0x6d1b1a(_0x5bcbe8._0x5f0c34)](/\b(the|a|an)\b/g,'')[_0x6d1b1a(_0x5bcbe8._0x18539b)](/[:\-_]/g,'\x20')[_0x6d1b1a(_0x5bcbe8._0xe6898a)](/\s+/g,'\x20')['replace'](/[^\w\s]/g,'')[_0x6d1b1a(_0x5bcbe8._0x26937b)]();}function calculateTitleSimilarity(_0x46b3e4,_0x1b01ae){const _0x2979ac={_0x54fa97:0x140,_0x2c55ac:0x161,_0x466689:0x149},_0x285d0c=_0x4cfe8c,_0xecd6c9=normalizeTitle(_0x46b3e4),_0x1ce152=normalizeTitle(_0x1b01ae);if(_0xecd6c9===_0x1ce152)return 0x1;const _0x497600=_0xecd6c9['split'](/\s+/)['filter'](_0x973f27=>_0x973f27['length']>0x0),_0x13b7d3=_0x1ce152['split'](/\s+/)['filter'](_0x3d5d0c=>_0x3d5d0c['length']>0x0);if(_0x497600[_0x285d0c(0x149)]===0x0||_0x13b7d3['length']===0x0)return 0x0;const _0x29dd94=new Set(_0x497600),_0x5c74c1=new Set(_0x13b7d3),_0x3778b0=_0x497600[_0x285d0c(0x161)](_0x394f3e=>_0x5c74c1[_0x285d0c(0xea)](_0x394f3e)),_0x296ff4=new Set([..._0x497600,..._0x13b7d3]),_0x315743=_0x3778b0['length']/_0x296ff4[_0x285d0c(_0x2979ac._0x54fa97)],_0x14fb85=_0x13b7d3[_0x285d0c(_0x2979ac._0x2c55ac)](_0x3d0b09=>!_0x29dd94[_0x285d0c(0xea)](_0x3d0b09))['length'];let _0x2872cd=_0x315743-_0x14fb85*0.05;return _0x497600[_0x285d0c(_0x2979ac._0x466689)]>0x0&&_0x497600['every'](_0x41c073=>_0x5c74c1['has'](_0x41c073))&&(_0x2872cd+=0.2),_0x2872cd;}function findBestTitleMatch(_0x40cb33,_0x280381,_0x4a7316,_0xd19fba){const _0x1bd18c={_0x259fa5:0x149,_0x2d4b86:0x157,_0x5b134f:0x113,_0x1c792d:0x12f,_0x461f94:0xef,_0x48b604:0xb3,_0x199a01:0x13a},_0x586de5=_0x4cfe8c;if(!_0x280381||_0x280381[_0x586de5(_0x1bd18c._0x259fa5)]===0x0)return null;let _0x136bdf=null,_0x14607c=0x0;for(const _0x550c70 of _0x280381){let _0x9de7ca=calculateTitleSimilarity(_0x40cb33['title'],_0x550c70['title']);if(_0x40cb33['year']&&_0x550c70['year']){const _0x528758=Math['abs'](_0x40cb33['year']-_0x550c70[_0x586de5(0xee)]);if(_0x528758===0x0)_0x9de7ca+=0.2;else{if(_0x528758<=0x1)_0x9de7ca+=0.1;else{if(_0x528758>0x5)_0x9de7ca-=0.3;}}}if(_0x4a7316==='tv'&&_0xd19fba){const _0x592c93=_0x550c70['title']['toLowerCase'](),_0x238fc7=[_0x586de5(0x143)+_0xd19fba,'s'+_0xd19fba,'season\x20'+_0xd19fba[_0x586de5(_0x1bd18c._0x2d4b86)]()[_0x586de5(0xaa)](0x2,'0'),'s'+_0xd19fba['toString']()['padStart'](0x2,'0')],_0x1e5c67=_0x238fc7[_0x586de5(0x11f)](_0xe07ba7=>_0x592c93['includes'](_0xe07ba7)),_0x58c61e=_0x592c93[_0x586de5(0x118)](/season\s*(\d+)|s(\d+)/i);if(_0x58c61e){const _0x23f41f=parseInt(_0x58c61e[0x1]||_0x58c61e[0x2]);_0x23f41f!==_0xd19fba&&(_0x9de7ca-=0.8);}if(_0x1e5c67)_0x9de7ca+=0.5;else _0x9de7ca-=0.3;}(_0x550c70['title'][_0x586de5(_0x1bd18c._0x5b134f)]()[_0x586de5(_0x1bd18c._0x1c792d)]('2160p')||_0x550c70['title']['toLowerCase']()['includes']('4k'))&&(_0x9de7ca+=0.05),_0x9de7ca>_0x14607c&&_0x9de7ca>0.3&&(_0x14607c=_0x9de7ca,_0x136bdf=_0x550c70);}if(_0x136bdf)console['log'](_0x586de5(_0x1bd18c._0x461f94)+_0x136bdf[_0x586de5(_0x1bd18c._0x48b604)]+_0x586de5(_0x1bd18c._0x199a01)+_0x14607c['toFixed'](0x2)+')');return _0x136bdf;}function getTMDBDetails(_0x30f6d5,_0x293f43){const _0x15db4c={_0x4d9e07:0x167,_0x4bc8d2:0x168,_0x521819:0x156,_0x45ae7f:0x13f,_0x1f42fe:0x16b};return __async(this,null,function*(){const _0x25ae9c=_0x1850;var _0x4e4372;const _0x39bb08=_0x293f43==='tv'?'tv':'movie',_0x2bdc62=TMDB_BASE_URL+'/'+_0x39bb08+'/'+_0x30f6d5+_0x25ae9c(_0x15db4c._0x4d9e07)+TMDB_API_KEY+_0x25ae9c(0xce),_0x2580ee=yield fetch(_0x2bdc62,{'method':_0x25ae9c(_0x15db4c._0x4bc8d2),'headers':{'Accept':'application/json','User-Agent':_0x25ae9c(_0x15db4c._0x521819)}});if(!_0x2580ee['ok'])throw new Error('TMDB\x20API\x20error:\x20'+_0x2580ee['status']);const _0x35e068=yield _0x2580ee['json'](),_0x4179c8=_0x293f43==='tv'?_0x35e068['name']:_0x35e068['title'],_0x291a1d=_0x293f43==='tv'?_0x35e068[_0x25ae9c(0xc0)]:_0x35e068[_0x25ae9c(_0x15db4c._0x45ae7f)],_0x316a55=_0x291a1d?parseInt(_0x291a1d['split']('-')[0x0]):null;return{'title':_0x4179c8,'year':_0x316a55,'imdbId':((_0x4e4372=_0x35e068[_0x25ae9c(_0x15db4c._0x1f42fe)])==null?void 0x0:_0x4e4372[_0x25ae9c(0xe2)])||null};});}var import_cheerio_without_node_native=__toESM(require(_0x4cfe8c(0x102))),import_crypto_js=__toESM(require('crypto-js'));function _0x1850(_0x567d81,_0x4c4e1a){_0x567d81=_0x567d81-0xa9;const _0x1d4126=_0x1d41();let _0x1850c2=_0x1d4126[_0x567d81];if(_0x1850['fiuDPA']===undefined){var _0x1f6823=function(_0x56ba7f){const _0x2a9730='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x88bbc8='',_0x59e2f6='';for(let _0x38ec05=0x0,_0x586ac9,_0x243eff,_0x4d4ed6=0x0;_0x243eff=_0x56ba7f['charAt'](_0x4d4ed6++);~_0x243eff&&(_0x586ac9=_0x38ec05%0x4?_0x586ac9*0x40+_0x243eff:_0x243eff,_0x38ec05++%0x4)?_0x88bbc8+=String['fromCharCode'](0xff&_0x586ac9>>(-0x2*_0x38ec05&0x6)):0x0){_0x243eff=_0x2a9730['indexOf'](_0x243eff);}for(let _0x2528ff=0x0,_0x869b1a=_0x88bbc8['length'];_0x2528ff<_0x869b1a;_0x2528ff++){_0x59e2f6+='%'+('00'+_0x88bbc8['charCodeAt'](_0x2528ff)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x59e2f6);};_0x1850['yyHhXs']=_0x1f6823,_0x1850['GYhHjK']={},_0x1850['fiuDPA']=!![];}const _0x39d2c9=_0x1d4126[0x0],_0x330ae8=_0x567d81+_0x39d2c9,_0x1de25b=_0x1850['GYhHjK'][_0x330ae8];return!_0x1de25b?(_0x1850c2=_0x1850['yyHhXs'](_0x1850c2),_0x1850['GYhHjK'][_0x330ae8]=_0x1850c2):_0x1850c2=_0x1de25b,_0x1850c2;}function getRedirectLinks(_0x3a4a38){const _0x3d42ce={_0x91b740:0x12d,_0x2be88:0xc9,_0x31c3ba:0x154,_0x5467fc:0xf7,_0x363cc0:0x139,_0x45ded9:0xb9};return __async(this,null,function*(){const _0x2af61e=_0x1850;try{const _0x1dc9b2=yield fetch(_0x3a4a38,{'headers':HEADERS});if(!_0x1dc9b2['ok'])throw new Error('HTTP\x20'+_0x1dc9b2[_0x2af61e(_0x3d42ce._0x91b740)]+':\x20'+_0x1dc9b2[_0x2af61e(0xc4)]);const _0x330cbb=yield _0x1dc9b2[_0x2af61e(_0x3d42ce._0x2be88)](),_0x1b48f6=/s\s*\(\s*['"]o['"]\s*,\s*['"]([A-Za-z0-9+/=]+)['"]|ck\s*\(\s*['"]_wp_http_\d+['"]\s*,\s*['"]([^'"]+)['"]/g;let _0x151934='',_0x1b719f;while((_0x1b719f=_0x1b48f6[_0x2af61e(0x162)](_0x330cbb))!==null){const _0x5bfc8d=_0x1b719f[0x1]||_0x1b719f[0x2];if(_0x5bfc8d)_0x151934+=_0x5bfc8d;}if(!_0x151934){const _0x502bed=_0x330cbb[_0x2af61e(0x118)](/window\.location\.href\s*=\s*['"]([^'"]+)['"]/);if(_0x502bed&&_0x502bed[0x1]){const _0x19e414=_0x502bed[0x1];if(_0x19e414!==_0x3a4a38&&!_0x19e414[_0x2af61e(0x12f)](_0x3a4a38))return yield getRedirectLinks(_0x19e414);}return null;}const _0x42df4e=atob(rot13(atob(atob(_0x151934)))),_0x3f31d3=JSON['parse'](_0x42df4e),_0x1657a9=atob(_0x3f31d3['o']||'')[_0x2af61e(0xf7)]();if(_0x1657a9)return _0x1657a9;const _0x14ed66=atob(_0x3f31d3[_0x2af61e(_0x3d42ce._0x31c3ba)]||'')[_0x2af61e(_0x3d42ce._0x5467fc)](),_0x3e9646=(_0x3f31d3[_0x2af61e(_0x3d42ce._0x363cc0)]||'')[_0x2af61e(0xf7)]();if(_0x3e9646&&_0x14ed66){const _0x98b056=yield fetch(_0x3e9646+'?re='+_0x14ed66,{'headers':HEADERS}),_0x36ff79=yield _0x98b056[_0x2af61e(_0x3d42ce._0x2be88)](),_0x49af98=import_cheerio_without_node_native['default']['load'](_0x36ff79);return(_0x49af98(_0x2af61e(_0x3d42ce._0x45ded9))[_0x2af61e(0xc9)]()||_0x36ff79)[_0x2af61e(0xf7)]();}return null;}catch(_0x25d58d){return null;}});}function vidStackExtractor(_0x11edee){const _0xc14b88={_0x59755b:0x142,_0x5a8978:0xf7,_0x5b4df0:0x11d,_0x53849c:0x13c,_0x472c4b:0xd4,_0x6dc351:0x157,_0x44d8a9:0xdf};return __async(this,null,function*(){const _0x3f2a40=_0x1850;var _0x3223b7,_0x79fab5,_0x46f594;try{const _0x23102c=_0x11edee['split']('#')['pop']()['split']('/')[_0x3f2a40(0x11b)](),_0x5c88b3=new URL(_0x11edee)['origin'],_0x55ddcb=_0x5c88b3+_0x3f2a40(_0xc14b88._0x59755b)+_0x23102c,_0x57224b=yield fetch(_0x55ddcb,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x11edee})}),_0x1b50c1=(yield _0x57224b['text']())[_0x3f2a40(_0xc14b88._0x5a8978)](),_0x43e1b9=import_crypto_js[_0x3f2a40(0x128)][_0x3f2a40(0xae)][_0x3f2a40(0x14b)][_0x3f2a40(_0xc14b88._0x5b4df0)](_0x3f2a40(0x105)),_0x39fcda=[_0x3f2a40(_0xc14b88._0x53849c),_0x3f2a40(0x100)];for(const _0x3b8c36 of _0x39fcda){try{const _0x479c4a=import_crypto_js['default'][_0x3f2a40(0xae)][_0x3f2a40(0x14b)][_0x3f2a40(0x11d)](_0x3b8c36),_0x2965ff=import_crypto_js['default']['AES']['decrypt']({'ciphertext':import_crypto_js['default']['enc'][_0x3f2a40(_0xc14b88._0x472c4b)][_0x3f2a40(0x11d)](_0x1b50c1)},_0x43e1b9,{'iv':_0x479c4a,'mode':import_crypto_js['default']['mode'][_0x3f2a40(0x110)],'padding':import_crypto_js[_0x3f2a40(0x128)]['pad']['Pkcs7']}),_0x2baea8=_0x2965ff[_0x3f2a40(_0xc14b88._0x6dc351)](import_crypto_js[_0x3f2a40(0x128)][_0x3f2a40(0xae)][_0x3f2a40(0x14b)]);if(_0x2baea8&&_0x2baea8['includes'](_0x3f2a40(_0xc14b88._0x44d8a9))){const _0x18f56d=(_0x79fab5=(_0x3223b7=_0x2baea8['match'](/"source":"(.*?)"/))==null?void 0x0:_0x3223b7[0x1])==null?void 0x0:_0x79fab5['replace'](/\\/g,''),_0x415a15=[],_0x3f7223=(_0x46f594=_0x2baea8['match'](/"subtitle":\{(.*?)\}/))==null?void 0x0:_0x46f594[0x1];if(_0x3f7223){const _0x305160=/"([^"]+)":\s*"([^"]+)"/g;let _0x5d18fa;while((_0x5d18fa=_0x305160['exec'](_0x3f7223))!==null){const _0x808ee3=_0x5d18fa[0x1],_0x3e50c2=_0x5d18fa[0x2]['split']('#')[0x0][_0x3f2a40(0x112)](/\\/g,'');_0x3e50c2&&_0x415a15['push']({'language':_0x808ee3,'url':_0x3e50c2[_0x3f2a40(0xd6)]('http')?_0x3e50c2:''+_0x5c88b3+_0x3e50c2});}}if(_0x18f56d)return[{'source':'Vidstack\x20Hubstream','quality':_0x3f2a40(0xcb),'url':_0x18f56d['replace']('https:','http:'),'headers':{'Referer':_0x11edee,'Origin':_0x11edee['split']('/')[_0x3f2a40(0x11b)]()},'subtitles':_0x415a15}];}}catch(_0x5d46c8){}}return[];}catch(_0x4ea3d9){return[];}});}function hbLinksExtractor(_0x1b96b2){const _0x672eee={_0x90bf4c:0x128,_0x50f821:0xe9};return __async(this,null,function*(){const _0x5c90df=_0x1850;try{const _0x1b2fba=yield fetch(_0x1b96b2,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x1b96b2})}),_0xf11254=yield _0x1b2fba['text'](),_0xaaa57f=import_cheerio_without_node_native[_0x5c90df(_0x672eee._0x90bf4c)][_0x5c90df(0x165)](_0xf11254),_0xe0515a=_0xaaa57f('h3\x20a,\x20h5\x20a,\x20div.entry-content\x20p\x20a')['map']((_0x14f8b3,_0x38ee5b)=>_0xaaa57f(_0x38ee5b)['attr']('href'))[_0x5c90df(_0x672eee._0x50f821)](),_0x295da5=yield Promise[_0x5c90df(0xcf)](_0xe0515a['map'](_0x438144=>loadExtractor(_0x438144,_0x1b96b2)));return _0x295da5['flat']()['map'](_0x57c356=>__spreadProps(__spreadValues({},_0x57c356),{'source':_0x57c356['source']+_0x5c90df(0xc8)}));}catch(_0x9238c2){return[];}});}function pixelDrainExtractor(_0x1a2bd7){const _0x274678={_0x2f5ac0:0xd2,_0x546ad9:0xd7};return __async(this,null,function*(){const _0x71334a=_0x1850;var _0x155c03;try{const _0xe2832d=new URL(_0x1a2bd7),_0x324dba=_0xe2832d[_0x71334a(_0x274678._0x2f5ac0)]+'//'+_0xe2832d[_0x71334a(0x159)],_0x1f4e3f=((_0x155c03=_0x1a2bd7['match'](/(?:file|u)\/([A-Za-z0-9]+)/))==null?void 0x0:_0x155c03[0x1])||_0x1a2bd7[_0x71334a(_0x274678._0x546ad9)]('/')['pop']();if(!_0x1f4e3f)return[{'source':_0x71334a(0x158),'quality':0x0,'url':_0x1a2bd7}];const _0x40bab5=_0x1a2bd7['includes'](_0x71334a(0xf3))?_0x1a2bd7:_0x324dba+'/api/file/'+_0x1f4e3f+_0x71334a(0xf3);return[{'source':'Pixeldrain','quality':0x0,'url':_0x40bab5}];}catch(_0x2cb417){return[{'source':'Pixeldrain','quality':0x0,'url':_0x1a2bd7}];}});}function streamTapeExtractor(_0x1f9c4f){const _0x1897ea={_0x512ff2:0x144,_0x1105ed:0x118};return __async(this,null,function*(){const _0x1e28c3=_0x1850;var _0x49aaa2,_0x5c07ff,_0x2c8792,_0x400c37;try{const _0x1146bd=new URL(_0x1f9c4f);_0x1146bd[_0x1e28c3(0x159)]=_0x1e28c3(_0x1897ea._0x512ff2);const _0x1206a3=yield fetch(_0x1146bd['toString'](),{'headers':HEADERS}),_0x4a5441=yield _0x1206a3['text']();let _0x4a3557=(_0x2c8792=(_0x5c07ff=(_0x49aaa2=_0x4a5441[_0x1e28c3(0x118)](/document\.getElementById\('videolink'\)\.innerHTML = (.*?);/))==null?void 0x0:_0x49aaa2[0x1])==null?void 0x0:_0x5c07ff[_0x1e28c3(_0x1897ea._0x1105ed)](/'(\/\/streamtape\.com\/get_video[^']+)'/))==null?void 0x0:_0x2c8792[0x1];return!_0x4a3557&&(_0x4a3557=(_0x400c37=_0x4a5441[_0x1e28c3(0x118)](/'(\/\/streamtape\.com\/get_video[^']+)'/))==null?void 0x0:_0x400c37[0x1]),_0x4a3557?[{'source':'StreamTape','quality':0x2d0,'url':'https:'+_0x4a3557}]:[];}catch(_0x2afe28){return[];}});}function hubCloudExtractor(_0x40be9e,_0x4b466f){const _0x2be4f1={_0x353b42:0x12f,_0x9e4a75:0xc7,_0x1f63e4:0x149,_0xba947a:0x14a,_0x387860:0x118,_0x1e34c5:0xc9,_0x963340:0x165,_0x491e49:0x132,_0x30d1a6:0xf7,_0x11cb7b:0xc9,_0x709fae:0x134,_0x3e1f70:0x12f,_0x48fc4d:0xbc,_0x1c87b1:0x148,_0x238337:0x12f,_0xf7cea7:0xfc,_0x24ced6:0x15d,_0x33cf53:0x169,_0x56423c:0xe9,_0x5d7055:0xc1,_0x3df873:0xac,_0x3ba68e:0x101,_0x2d94ca:0x104,_0x3c3bc8:0xe7,_0x1c7b8c:0xb6};return __async(this,null,function*(){const _0x18fe85=_0x1850;var _0x3b7b60;try{let _0x2e9567=_0x40be9e['replace'](_0x18fe85(0x13b),'hubcloud.dad');const _0x44ad7f=yield fetch(_0x2e9567,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x4b466f})});let _0x3c42ab=yield _0x44ad7f['text'](),_0x1f1731=_0x2e9567;if(!_0x2e9567[_0x18fe85(_0x2be4f1._0x353b42)]('hubcloud.php')){let _0x5c5b56='';const _0x658c85=import_cheerio_without_node_native['default']['load'](_0x3c42ab),_0x506a69=_0x658c85(_0x18fe85(_0x2be4f1._0x9e4a75));if(_0x506a69[_0x18fe85(_0x2be4f1._0x1f63e4)])_0x5c5b56=_0x506a69['attr'](_0x18fe85(_0x2be4f1._0xba947a));else{const _0x18fdae=_0x3c42ab[_0x18fe85(_0x2be4f1._0x387860)](/var url = '([^']*)'/);if(_0x18fdae)_0x5c5b56=_0x18fdae[0x1];}if(_0x5c5b56){if(!_0x5c5b56[_0x18fe85(0xd6)](_0x18fe85(0xe6))){const _0x11f1f5=new URL(_0x2e9567);_0x5c5b56=_0x11f1f5['protocol']+'//'+_0x11f1f5[_0x18fe85(0x159)]+'/'+_0x5c5b56['replace'](/^\//,'');}_0x1f1731=_0x5c5b56;const _0x3f741f=yield fetch(_0x1f1731,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x2e9567})});_0x3c42ab=yield _0x3f741f[_0x18fe85(_0x2be4f1._0x1e34c5)]();}}const _0x26900c=import_cheerio_without_node_native['default'][_0x18fe85(_0x2be4f1._0x963340)](_0x3c42ab),_0x4a5266=_0x26900c(_0x18fe85(_0x2be4f1._0x491e49))[_0x18fe85(_0x2be4f1._0x1e34c5)]()['trim'](),_0x7cdd77=_0x26900c('div.card-header')[_0x18fe85(_0x2be4f1._0x1e34c5)]()[_0x18fe85(_0x2be4f1._0x30d1a6)](),_0x35c35d=(_0x3b7b60=_0x7cdd77[_0x18fe85(_0x2be4f1._0x387860)](/(\d{3,4})[pP]/))==null?void 0x0:_0x3b7b60[0x1],_0x4d5130=_0x35c35d?parseInt(_0x35c35d):0x438,_0x586be9=cleanTitle(_0x7cdd77),_0x106853=(_0x586be9?'['+_0x586be9+']':'')+(_0x4a5266?'['+_0x4a5266+']':''),_0x3c4587=((()=>{const _0x3f0983=_0x4a5266['match'](/([\d.]+)\s*(GB|MB|KB)/i);if(!_0x3f0983)return 0x0;const _0x4e08f2={'GB':0x400**0x3,'MB':0x400**0x2,'KB':0x400};return parseFloat(_0x3f0983[0x1])*(_0x4e08f2[_0x3f0983[0x2]['toUpperCase']()]||0x0);})()),_0x349f68=[],_0x274ffe=_0x26900c('a.btn')['get']();for(const _0x2eeba4 of _0x274ffe){const _0x4e6ddb=_0x26900c(_0x2eeba4)['attr'](_0x18fe85(0x14a)),_0x28f39b=_0x26900c(_0x2eeba4)[_0x18fe85(_0x2be4f1._0x11cb7b)]()[_0x18fe85(0x113)](),_0x30238b=_0x7cdd77||_0x586be9||'Unknown';if(_0x28f39b['includes']('download\x20file')||_0x28f39b['includes'](_0x18fe85(0x150))||_0x28f39b[_0x18fe85(_0x2be4f1._0x353b42)](_0x18fe85(_0x2be4f1._0x709fae))||_0x28f39b['includes']('fslv2')||_0x28f39b[_0x18fe85(0x12f)]('mega\x20server')||_0x4e6ddb&&_0x4e6ddb[_0x18fe85(_0x2be4f1._0x3e1f70)](_0x18fe85(_0x2be4f1._0x48fc4d))){let _0x148366=_0x18fe85(_0x2be4f1._0x1c87b1);if(_0x4e6ddb&&_0x4e6ddb['includes']('r2.dev'))_0x148366=_0x18fe85(0x129);else{if(_0x4e6ddb&&_0x4e6ddb[_0x18fe85(_0x2be4f1._0x238337)]('workers.dev'))_0x148366=_0x18fe85(0xfb);else{if(_0x28f39b[_0x18fe85(0x12f)](_0x18fe85(0x150)))_0x148366=_0x18fe85(_0x2be4f1._0xf7cea7);else{if(_0x28f39b['includes'](_0x18fe85(0x134)))_0x148366='HubCloud\x20-\x20S3';else{if(_0x28f39b[_0x18fe85(_0x2be4f1._0x353b42)](_0x18fe85(0x14e)))_0x148366='HubCloud\x20-\x20FSLv2';else{if(_0x28f39b[_0x18fe85(_0x2be4f1._0x3e1f70)]('mega\x20server'))_0x148366='HubCloud\x20-\x20Mega';}}}}}_0x349f68[_0x18fe85(0xb6)]({'source':_0x148366+'\x20'+_0x106853,'quality':_0x4d5130,'url':_0x4e6ddb,'size':_0x3c4587,'fileName':_0x30238b});}else{if(_0x28f39b['includes']('buzzserver'))try{const _0x2c3c73=yield fetch(_0x4e6ddb+_0x18fe85(0x11c),{'method':'GET','headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x4e6ddb}),'redirect':_0x18fe85(_0x2be4f1._0x24ced6)});let _0x519976=_0x2c3c73['headers'][_0x18fe85(0xe9)](_0x18fe85(0x12e))||_0x2c3c73[_0x18fe85(_0x2be4f1._0x33cf53)][_0x18fe85(_0x2be4f1._0x56423c)](_0x18fe85(0xf6));!_0x519976&&_0x2c3c73['url']&&_0x2c3c73['url']!==_0x4e6ddb+_0x18fe85(0x11c)&&(_0x519976=_0x2c3c73[_0x18fe85(_0x2be4f1._0x5d7055)]),_0x519976&&_0x349f68['push']({'source':'HubCloud\x20-\x20BuzzServer\x20'+_0x106853,'quality':_0x4d5130,'url':_0x519976,'size':_0x3c4587,'fileName':_0x30238b});}catch(_0x40c8a9){}else{if(_0x28f39b['includes']('10gbps')||_0x4e6ddb&&_0x4e6ddb[_0x18fe85(_0x2be4f1._0x353b42)](_0x18fe85(0xfe))){let _0x567c2e=_0x4e6ddb;if(_0x4e6ddb&&!_0x4e6ddb['includes'](_0x18fe85(0xfe)))try{const _0x3abc77=yield fetch(_0x4e6ddb,{'method':'GET','redirect':_0x18fe85(0x15d)}),_0x1e3af5=_0x3abc77['headers']['get'](_0x18fe85(_0x2be4f1._0x3df873));_0x1e3af5&&_0x1e3af5[_0x18fe85(0x12f)](_0x18fe85(0x104))&&(_0x567c2e=_0x1e3af5[_0x18fe85(_0x2be4f1._0x3ba68e)](_0x1e3af5['indexOf'](_0x18fe85(_0x2be4f1._0x2d94ca))+0x5));}catch(_0x8aa1e5){}_0x349f68['push']({'source':_0x18fe85(0x111)+_0x106853,'quality':_0x4d5130,'url':_0x567c2e,'size':_0x3c4587,'fileName':_0x30238b});}else{if(_0x28f39b['includes'](_0x18fe85(_0x2be4f1._0x3c3bc8))||_0x4e6ddb&&_0x4e6ddb['includes']('workers.dev'))_0x349f68['push']({'source':_0x18fe85(0x163)+_0x106853,'quality':_0x4d5130,'url':_0x4e6ddb,'size':_0x3c4587,'fileName':_0x30238b});else{if(_0x4e6ddb&&_0x4e6ddb['includes'](_0x18fe85(0xc2))){const _0x28c01d=yield pixelDrainExtractor(_0x4e6ddb);_0x349f68['push'](..._0x28c01d['map'](_0x3d631e=>__spreadProps(__spreadValues({},_0x3d631e),{'source':_0x3d631e['source']+'\x20'+_0x106853,'size':_0x3c4587,'fileName':_0x30238b})));}else{if(_0x4e6ddb&&!_0x4e6ddb['includes'](_0x18fe85(0xe4))&&_0x4e6ddb[_0x18fe85(0xd6)]('http')){const _0x269814=yield loadExtractor(_0x4e6ddb,_0x1f1731);_0x349f68[_0x18fe85(_0x2be4f1._0x1c7b8c)](..._0x269814['map'](_0x38c29f=>__spreadProps(__spreadValues({},_0x38c29f),{'quality':_0x38c29f['quality']||_0x4d5130})));}}}}}}}return _0x349f68;}catch(_0x5b5815){return[];}});}function hubCdnExtractor(_0x57f16d,_0x156a2d){const _0x82767d={_0x5bf069:0x122,_0x2204cc:0x104,_0x1ce294:0xe6,_0x5bb782:0xd7,_0x31c1eb:0xd6,_0x1c3dca:0x118,_0x29deb6:0xd6},_0x369509={_0x3ebd90:0x13d,_0x36ba1f:0x12f,_0x48296d:0x131};return __async(this,null,function*(){const _0x22b631=_0x1850;try{const _0x308477=yield fetch(_0x57f16d,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x156a2d})}),_0x25a016=yield _0x308477[_0x22b631(0xc9)](),_0x21ed9a=import_cheerio_without_node_native['default']['load'](_0x25a016);let _0x2fe83e='';_0x21ed9a('script')['each']((_0x4485ae,_0x461b7d)=>{const _0xb4d551=_0x22b631,_0x578952=_0x21ed9a(_0x461b7d)[_0xb4d551(_0x369509._0x3ebd90)]();_0x578952&&_0x578952[_0xb4d551(_0x369509._0x36ba1f)](_0xb4d551(_0x369509._0x48296d))&&(_0x2fe83e=_0x578952);});if(_0x2fe83e){const _0x3c4c92=_0x2fe83e['match'](/reurl\s*=\s*["']([^"']+)["']/);if(_0x3c4c92&&_0x3c4c92[0x1]){const _0x14caa4=_0x3c4c92[0x1];if(_0x14caa4['includes']('?r=')){const _0x3f8999=_0x14caa4['split']('?r=')['pop']();try{const _0x34087c=atob(_0x3f8999),_0x584606=_0x34087c[_0x22b631(0x101)](_0x34087c[_0x22b631(_0x82767d._0x5bf069)](_0x22b631(_0x82767d._0x2204cc))+0x5);if(_0x584606&&_0x584606[_0x22b631(0xd6)](_0x22b631(_0x82767d._0x1ce294)))return[{'source':'HubCdn','quality':0x438,'url':_0x584606}];}catch(_0xa2f973){}}else{if(_0x14caa4['includes'](_0x22b631(0x104))){const _0x577557=_0x14caa4[_0x22b631(_0x82767d._0x5bb782)](_0x22b631(0x104))['pop']();if(_0x577557&&_0x577557['startsWith'](_0x22b631(0xe6)))return[{'source':'HubCdn','quality':0x438,'url':_0x577557}];}else{if(_0x14caa4[_0x22b631(_0x82767d._0x31c1eb)](_0x22b631(_0x82767d._0x1ce294)))return[{'source':_0x22b631(0x108),'quality':0x438,'url':_0x14caa4}];}}}}const _0x57b4da=_0x25a016[_0x22b631(_0x82767d._0x1c3dca)](/r=([A-Za-z0-9+/=]+)/);if(_0x57b4da&&_0x57b4da[0x1])try{const _0x44d334=atob(_0x57b4da[0x1]),_0x330cb5=_0x44d334['substring'](_0x44d334['lastIndexOf'](_0x22b631(0x104))+0x5);if(_0x330cb5&&_0x330cb5[_0x22b631(_0x82767d._0x29deb6)]('http'))return[{'source':_0x22b631(0x108),'quality':0x438,'url':_0x330cb5}];}catch(_0x4ec171){}return[];}catch(_0x99eac8){return[];}});}function loadExtractor(_0x37f613){const _0xc43b91={_0x651fc2:0xbb,_0x1ead00:0x141,_0x2873de:0x155,_0x45e8ef:0xe8,_0xfe189f:0x12f,_0x3d31bb:0x15a,_0xc56c1f:0x12f,_0x440e78:0xdc,_0x224390:0x12f,_0xf7ef73:0x165};return __async(this,arguments,function*(_0x43a854,_0x38a20c=MAIN_URL){const _0xd5fd69=_0x1850;try{const _0x7e64e9=new URL(_0x43a854)['hostname'],_0x32c947=_0x43a854['includes'](_0xd5fd69(_0xc43b91._0x651fc2))||_0x7e64e9['includes'](_0xd5fd69(_0xc43b91._0x1ead00))||_0x7e64e9['includes'](_0xd5fd69(_0xc43b91._0x2873de))||_0x7e64e9[_0xd5fd69(0x12f)](_0xd5fd69(_0xc43b91._0x45e8ef))||_0x7e64e9[_0xd5fd69(_0xc43b91._0xfe189f)]('bloggingvector')||_0x7e64e9['includes']('ampproject.org');if(_0x32c947){const _0x3c4d34=yield getRedirectLinks(_0x43a854);if(_0x3c4d34&&_0x3c4d34!==_0x43a854)return yield loadExtractor(_0x3c4d34,_0x43a854);return[];}if(_0x7e64e9['includes']('hubcloud'))return yield hubCloudExtractor(_0x43a854,_0x38a20c);if(_0x7e64e9['includes'](_0xd5fd69(_0xc43b91._0x3d31bb)))return yield hubCdnExtractor(_0x43a854,_0x38a20c);if(_0x7e64e9['includes']('hblinks')||_0x7e64e9[_0xd5fd69(_0xc43b91._0xc56c1f)]('hubstream.dad'))return yield hbLinksExtractor(_0x43a854);if(_0x7e64e9['includes']('hubstream')||_0x7e64e9['includes']('vidstack'))return yield vidStackExtractor(_0x43a854);if(_0x7e64e9[_0xd5fd69(0x12f)]('pixeldrain'))return yield pixelDrainExtractor(_0x43a854);if(_0x7e64e9[_0xd5fd69(0x12f)]('streamtape'))return yield streamTapeExtractor(_0x43a854);if(_0x7e64e9['includes'](_0xd5fd69(_0xc43b91._0x440e78)))return[{'source':_0xd5fd69(0x164),'quality':0x438,'url':_0x43a854}];if(_0x7e64e9[_0xd5fd69(_0xc43b91._0x224390)]('hubdrive')){const _0xd2fc4f=yield fetch(_0x43a854,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x38a20c})}),_0x2bb502=yield _0xd2fc4f['text'](),_0x52fa9f=import_cheerio_without_node_native['default'][_0xd5fd69(_0xc43b91._0xf7ef73)](_0x2bb502)('.btn.btn-primary.btn-user.btn-success1.m-1')[_0xd5fd69(0x147)](_0xd5fd69(0x14a));if(_0x52fa9f)return yield loadExtractor(_0x52fa9f,_0x43a854);}return[];}catch(_0x42387d){return[];}});}function search(_0x4050e0){const _0x18a073={_0x361da1:0xd7,_0xebeed8:0xe3,_0x3aebc6:0xf8};return __async(this,null,function*(){const _0x19d7d5={_0x147b22:0x107,_0x309bdf:0xd5,_0x11cdb1:0xd6,_0x4c4e6c:0xb0},_0x34c9c6=_0x1850,_0x394053=new Date()['toISOString']()[_0x34c9c6(_0x18a073._0x361da1)]('T')[0x0],_0x54245b=_0x34c9c6(_0x18a073._0xebeed8)+encodeURIComponent(_0x4050e0)+'&query_by=post_title,category&query_by_weights=4,2&sort_by=sort_by_date:desc&limit=15&highlight_fields=none&use_cache=true&page=1&analytics_tag='+_0x394053,_0x3ce9c9=yield fetch(_0x54245b,{'headers':HEADERS}),_0x4de085=yield _0x3ce9c9['json']();if(!_0x4de085||!_0x4de085[_0x34c9c6(0x119)])return[];return _0x4de085[_0x34c9c6(0x119)][_0x34c9c6(_0x18a073._0x3aebc6)](_0xdf65e0=>{const _0x540e6a=_0x34c9c6,_0x4b6532=_0xdf65e0['document'],_0x630153=_0x4b6532[_0x540e6a(_0x19d7d5._0x147b22)],_0x59fa7c=_0x630153[_0x540e6a(0x118)](/\((\d{4})\)|\b(\d{4})\b/),_0x5a819d=_0x59fa7c?parseInt(_0x59fa7c[0x1]||_0x59fa7c[0x2]):null;let _0x352428=_0x4b6532[_0x540e6a(_0x19d7d5._0x309bdf)];return _0x352428&&_0x352428[_0x540e6a(_0x19d7d5._0x11cdb1)]('/')&&(_0x352428=''+MAIN_URL+_0x352428),{'title':_0x630153,'url':_0x352428,'poster':_0x4b6532[_0x540e6a(_0x19d7d5._0x4c4e6c)],'year':_0x5a819d};});});}function getDownloadLinks(_0x37ecb2){const _0x244e8d={_0x51d6fd:0x159,_0x53f372:0x165,_0x903b65:0x130,_0x1d8417:0x12f,_0x3807b2:0x153,_0x2907d7:0xf8,_0x2a8202:0xe9,_0x5ebc1a:0xcf,_0x5becc8:0x149,_0xb58748:0xfd},_0x4f0384={_0x3fb8c6:0xc1,_0x2cf72e:0x12f,_0x5eb2f9:0xca},_0x2e7d99={_0x1909a6:0xb6},_0x2d15bc={_0x294953:0xbf,_0x4fc8a9:0xf8,_0x4be1b3:0xb6,_0x272b27:0xe9},_0x2d5f59={_0x3bab7c:0x113,_0x4f77b6:0x12f},_0x5f0d72={_0x3bee9e:0x14a,_0x22c9f2:0xdc,_0x1f1e6d:0x12f};return __async(this,null,function*(){const _0x518efc={_0x462412:0xc1},_0x5165ce={_0x438d3b:0xd3,_0x1a3700:0xbd},_0x2f3123=_0x1850,_0x491a83=yield getCurrentDomain();if(_0x37ecb2['includes']('hdhub4u.'))try{const _0x5aa80e=new URL(_0x37ecb2),_0x191c64=new URL(_0x491a83);_0x5aa80e[_0x2f3123(0x159)]=_0x191c64[_0x2f3123(_0x244e8d._0x51d6fd)],_0x37ecb2=_0x5aa80e['toString']();}catch(_0x14960f){}const _0x2977be=yield fetch(_0x37ecb2,{'headers':__spreadProps(__spreadValues({},HEADERS),{'Referer':_0x491a83+'/'})}),_0x203f07=yield _0x2977be['text'](),_0x346a06=import_cheerio_without_node_native2['default'][_0x2f3123(_0x244e8d._0x53f372)](_0x203f07),_0x1aac06=_0x346a06(_0x2f3123(_0x244e8d._0x903b65))['text'](),_0xfa4a85=_0x1aac06[_0x2f3123(0x113)]()[_0x2f3123(_0x244e8d._0x1d8417)](_0x2f3123(0x152));if(_0xfa4a85){const _0x774e1a=_0x346a06(_0x2f3123(_0x244e8d._0x3807b2))['filter']((_0x3d8871,_0x4e83cc)=>_0x346a06(_0x4e83cc)[_0x2f3123(0xc9)]()[_0x2f3123(0x118)](/480|720|1080|2160|4K/i)),_0x44a955=_0x346a06(_0x2f3123(0xf4))[_0x2f3123(0x161)]((_0x3a4cf4,_0x275fe2)=>{const _0x58f8c1=_0x2f3123,_0x370ccf=_0x346a06(_0x275fe2)['attr'](_0x58f8c1(_0x5f0d72._0x3bee9e));return _0x370ccf&&(_0x370ccf['includes'](_0x58f8c1(_0x5f0d72._0x22c9f2))||_0x370ccf[_0x58f8c1(_0x5f0d72._0x1f1e6d)]('hubstream'));}),_0x15f8f2=[...new Set([..._0x774e1a[_0x2f3123(_0x244e8d._0x2907d7)]((_0x1f7992,_0x12e5c0)=>_0x346a06(_0x12e5c0)['attr'](_0x2f3123(0x14a)))['get'](),..._0x44a955['map']((_0x3c1e41,_0x189e8f)=>_0x346a06(_0x189e8f)[_0x2f3123(0x147)](_0x2f3123(0x14a)))[_0x2f3123(_0x244e8d._0x2a8202)]()])],_0x222f1b=yield Promise[_0x2f3123(_0x244e8d._0x5ebc1a)](_0x15f8f2[_0x2f3123(0xf8)](_0x69d139=>loadExtractor(_0x69d139,_0x37ecb2))),_0x56430f=_0x222f1b['flat'](),_0x34f06a=new Set(),_0x57c441=_0x56430f[_0x2f3123(0x161)](_0x143ac2=>{const _0x4076c7=_0x2f3123;var _0x304ddb;if(!_0x143ac2[_0x4076c7(0xc1)]||_0x143ac2[_0x4076c7(0xc1)]['includes']('.zip')||((_0x304ddb=_0x143ac2[_0x4076c7(0x160)])==null?void 0x0:_0x304ddb[_0x4076c7(_0x2d5f59._0x3bab7c)]()[_0x4076c7(_0x2d5f59._0x4f77b6)]('.zip')))return![];if(_0x34f06a['has'](_0x143ac2['url']))return![];return _0x34f06a['add'](_0x143ac2['url']),!![];});return{'finalLinks':_0x57c441,'isMovie':_0xfa4a85};}else{const _0x12e458=new Map(),_0x3b176b=[];_0x346a06('h3,\x20h4')['each']((_0x49cf27,_0x8a1934)=>{const _0x389fd7=_0x2f3123,_0xe47dfc=_0x346a06(_0x8a1934),_0x1f94a4=_0xe47dfc['text'](),_0x55ff00=_0xe47dfc[_0x389fd7(_0x2d15bc._0x294953)]('a'),_0x590ec1=_0x55ff00[_0x389fd7(_0x2d15bc._0x4fc8a9)]((_0x29bfd9,_0xb4c1e4)=>_0x346a06(_0xb4c1e4)[_0x389fd7(0x147)](_0x389fd7(0x14a)))['get'](),_0x45ebb7=_0x55ff00[_0x389fd7(0xe9)]()[_0x389fd7(0x11f)](_0x9ebf90=>_0x346a06(_0x9ebf90)['text']()[_0x389fd7(0x118)](/1080|720|4K|2160/i));if(_0x45ebb7){_0x3b176b[_0x389fd7(_0x2d15bc._0x4be1b3)](..._0x590ec1);return;}const _0x1f5588=_0x1f94a4['match'](/(?:EPiSODE\s*(\d+)|E(\d+))/i);if(_0x1f5588){const _0x5cd6c6=parseInt(_0x1f5588[0x1]||_0x1f5588[0x2]);if(!_0x12e458['has'](_0x5cd6c6))_0x12e458[_0x389fd7(0x127)](_0x5cd6c6,[]);_0x12e458['get'](_0x5cd6c6)[_0x389fd7(_0x2d15bc._0x4be1b3)](..._0x590ec1);let _0x492e9c=_0xe47dfc[_0x389fd7(0xed)]();while(_0x492e9c['length']&&_0x492e9c[_0x389fd7(_0x2d15bc._0x272b27)](0x0)['tagName']!=='hr'){const _0x34c9f5=_0x492e9c[_0x389fd7(0xbf)]('a[href]')[_0x389fd7(_0x2d15bc._0x4fc8a9)]((_0x1e5376,_0x2755f6)=>_0x346a06(_0x2755f6)[_0x389fd7(0x147)]('href'))[_0x389fd7(0xe9)]();_0x12e458[_0x389fd7(_0x2d15bc._0x272b27)](_0x5cd6c6)['push'](..._0x34c9f5),_0x492e9c=_0x492e9c['next']();}}});_0x3b176b[_0x2f3123(_0x244e8d._0x5becc8)]>0x0&&(yield Promise['all'](_0x3b176b[_0x2f3123(_0x244e8d._0x2907d7)](_0x109f62=>__async(this,null,function*(){const _0x406122={_0x5cad47:0x147,_0x575e3c:0x14a,_0x6b4aaf:0xb6},_0x319fd8=_0x2f3123;try{const _0x325ae7=yield getRedirectLinks(_0x109f62);if(!_0x325ae7)return;const _0x588f94=yield fetch(_0x325ae7,{'headers':HEADERS}),_0x3b516e=yield _0x588f94['text'](),_0xe62e14=import_cheerio_without_node_native2['default'][_0x319fd8(0x165)](_0x3b516e);_0xe62e14(_0x319fd8(_0x5165ce._0x438d3b))[_0x319fd8(_0x5165ce._0x1a3700)]((_0x475367,_0x238ad0)=>{const _0x26dcb7=_0x319fd8,_0x36f923=_0xe62e14(_0x238ad0)[_0x26dcb7(0xc9)](),_0x404524=_0xe62e14(_0x238ad0)[_0x26dcb7(_0x406122._0x5cad47)](_0x26dcb7(_0x406122._0x575e3c)),_0x5d2f74=_0x36f923['match'](/Episode\s*(\d+)/i);if(_0x5d2f74&&_0x404524){const _0x21d8e0=parseInt(_0x5d2f74[0x1]);if(!_0x12e458['has'](_0x21d8e0))_0x12e458['set'](_0x21d8e0,[]);_0x12e458['get'](_0x21d8e0)[_0x26dcb7(_0x406122._0x6b4aaf)](_0x404524);}});}catch(_0x319d2a){}}))));const _0x1e0a42=[];_0x12e458['forEach']((_0x1387a7,_0x4127e4)=>{const _0x47f5e8=_0x2f3123,_0x1f018c=[...new Set(_0x1387a7)];_0x1e0a42[_0x47f5e8(_0x2e7d99._0x1909a6)](..._0x1f018c[_0x47f5e8(0xf8)](_0x374732=>({'url':_0x374732,'episode':_0x4127e4})));});const _0xe76bd9=yield Promise['all'](_0x1e0a42['map'](_0x11c525=>__async(this,null,function*(){const _0xac4085=_0x2f3123;try{const _0x280a57=yield loadExtractor(_0x11c525[_0xac4085(_0x518efc._0x462412)],_0x37ecb2);return _0x280a57['map'](_0x58e66c=>__spreadProps(__spreadValues({},_0x58e66c),{'episode':_0x11c525['episode']}));}catch(_0x16778a){return[];}}))),_0x2b3267=_0xe76bd9[_0x2f3123(_0x244e8d._0xb58748)](),_0x397162=new Set(),_0x19b4f0=_0x2b3267['filter'](_0x344da7=>{const _0x5cd943=_0x2f3123;if(!_0x344da7['url']||_0x344da7[_0x5cd943(_0x4f0384._0x3fb8c6)][_0x5cd943(_0x4f0384._0x2cf72e)](_0x5cd943(_0x4f0384._0x5eb2f9)))return![];if(_0x397162[_0x5cd943(0xea)](_0x344da7[_0x5cd943(_0x4f0384._0x3fb8c6)]))return![];return _0x397162[_0x5cd943(0x10b)](_0x344da7[_0x5cd943(_0x4f0384._0x3fb8c6)]),!![];});return{'finalLinks':_0x19b4f0,'isMovie':_0xfa4a85};}});}function getStreams(_0x6fb123,_0x44e130=_0x4cfe8c(0x152),_0xe589e2=null,_0x23aa96=null){const _0x2e7077={_0x18e96e:0x120,_0xc53699:0xcd,_0x4f5e33:0x137,_0x450da4:0xc1},_0x7ef8f={_0x4ba768:0xe0,_0x5d0aac:0xd0,_0x2ba8df:0xb3,_0x46fc7b:0xaa,_0x1fc576:0xaa,_0x8bc9a3:0x138,_0x2eca56:0x13e,_0x36a4bb:0x10f,_0x37b3e0:0xcc,_0x5e29c4:0x169,_0x3edd6f:0x15b};return __async(this,null,function*(){const _0x5aa329=_0x1850;console[_0x5aa329(_0x2e7077._0x18e96e)](_0x5aa329(_0x2e7077._0xc53699)+_0x6fb123+_0x5aa329(0x146)+_0x44e130);try{const _0x2fa81d=yield getTMDBDetails(_0x6fb123,_0x44e130);console['log'](_0x5aa329(0xc3)+_0x2fa81d['title']+'\x22\x20('+(_0x2fa81d[_0x5aa329(0xee)]||'N/A')+')');const _0x5add83=_0x44e130==='tv'&&_0xe589e2?_0x2fa81d['title']+_0x5aa329(_0x2e7077._0x4f5e33)+_0xe589e2:_0x2fa81d['title'],_0x424e15=yield search(_0x5add83);if(_0x424e15[_0x5aa329(0x149)]===0x0)return[];const _0x250433=findBestTitleMatch(_0x2fa81d,_0x424e15,_0x44e130,_0xe589e2),_0x8b1a29=_0x250433||_0x424e15[0x0];console[_0x5aa329(0x120)](_0x5aa329(0x135)+_0x8b1a29['title']+_0x5aa329(0xf1)+_0x8b1a29[_0x5aa329(_0x2e7077._0x450da4)]+')');const _0x256b26=yield getDownloadLinks(_0x8b1a29[_0x5aa329(0xc1)]),_0x163c3e=_0x256b26[_0x5aa329(0xad)];let _0x3cfcfe=_0x163c3e;_0x44e130==='tv'&&_0x23aa96!==null&&(_0x3cfcfe=_0x163c3e['filter'](_0x4f12c5=>_0x4f12c5[_0x5aa329(0x11e)]===_0x23aa96));const _0x1504d4=_0x3cfcfe[_0x5aa329(0xf8)](_0x4c046b=>{const _0x17024b=_0x5aa329;let _0x50686f=_0x4c046b['fileName']&&_0x4c046b[_0x17024b(_0x7ef8f._0x4ba768)]!==_0x17024b(_0x7ef8f._0x5d0aac)?_0x4c046b['fileName']:_0x2fa81d['title'];_0x44e130==='tv'&&_0xe589e2&&_0x23aa96&&(_0x50686f=_0x2fa81d[_0x17024b(_0x7ef8f._0x2ba8df)]+'\x20S'+String(_0xe589e2)[_0x17024b(_0x7ef8f._0x46fc7b)](0x2,'0')+'E'+String(_0x23aa96)[_0x17024b(_0x7ef8f._0x1fc576)](0x2,'0'));const _0x53d15f=extractServerName(_0x4c046b['source']);let _0x4acaf9='Unknown';if(typeof _0x4c046b['quality']===_0x17024b(0x10a)&&_0x4c046b['quality']>0x0){if(_0x4c046b['quality']>=0x870)_0x4acaf9='4K';else{if(_0x4c046b['quality']>=0x438)_0x4acaf9=_0x17024b(_0x7ef8f._0x8bc9a3);else{if(_0x4c046b['quality']>=0x2d0)_0x4acaf9=_0x17024b(0xf0);else{if(_0x4c046b[_0x17024b(0x10f)]>=0x1e0)_0x4acaf9='480p';}}}}else typeof _0x4c046b['quality']===_0x17024b(_0x7ef8f._0x2eca56)&&(_0x4acaf9=_0x4c046b[_0x17024b(_0x7ef8f._0x36a4bb)]);return{'name':_0x17024b(_0x7ef8f._0x37b3e0)+_0x53d15f,'title':_0x50686f,'url':_0x4c046b[_0x17024b(0xc1)],'quality':_0x4acaf9,'size':formatBytes(_0x4c046b['size']),'headers':_0x4c046b[_0x17024b(_0x7ef8f._0x5e29c4)]||void 0x0,'provider':_0x17024b(_0x7ef8f._0x3edd6f)};}),_0xa1c74={'4K':0x4,'1080p':0x2,'720p':0x1,'480p':0x0,'Unknown':-0x2};return _0x1504d4['sort']((_0x141dca,_0x5b99ad)=>(_0xa1c74[_0x5b99ad['quality']]||-0x3)-(_0xa1c74[_0x141dca[_0x5aa329(0x10f)]]||-0x3));}catch(_0x11c64c){return console['error']('[HDHub4u]\x20Scraping\x20error:\x20'+_0x11c64c['message']),[];}});}module[_0x4cfe8c(0x151)]={'getStreams':getStreams};
/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:1dc18f808c4e */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"baseUrl":"https://new4.hdhub4u.cl","providerName":"hdhub4u","maxAliases":8,"maxCandidates":8,"maxPlayers":8,"timeoutMs":7000,"budgetMs":45000,"languageHint":"","implementationRevision":"native-media-filename-identity-v3"});
/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:92bdb33cf8f8 */
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
  if(c.defaultUserAgent&&!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",c.defaultUserAgent);
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
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true,"defaultUserAgent":"","implementationRevision":"scoped-playback-context-v4"});
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:d6a36fd21307 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"hdhub4u","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
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
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":6500,"maxChildren":2,"maxRecoveryPages":4,"maxRecoveryCandidates":12,"implementationRevision":"recovery-first-v3"});
