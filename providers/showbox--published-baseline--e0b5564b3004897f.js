const _0x3cd342=_0x5e70;(function(_0x5bde39,_0x597b92){const _0x2a2d73={_0x5dff50:0x1f0,_0x468eb5:0x1f5,_0x24b78e:0x21e,_0x88db5e:0x244,_0x3cb3b3:0x20e,_0x1a0bf5:0x1de},_0x390e29=_0x5e70,_0x35abec=_0x5bde39();while(!![]){try{const _0x47cb6f=parseInt(_0x390e29(_0x2a2d73._0x5dff50))/0x1*(-parseInt(_0x390e29(0x23f))/0x2)+-parseInt(_0x390e29(_0x2a2d73._0x468eb5))/0x3+-parseInt(_0x390e29(0x1a7))/0x4*(parseInt(_0x390e29(0x22b))/0x5)+-parseInt(_0x390e29(0x249))/0x6*(-parseInt(_0x390e29(_0x2a2d73._0x24b78e))/0x7)+parseInt(_0x390e29(_0x2a2d73._0x88db5e))/0x8+parseInt(_0x390e29(_0x2a2d73._0x3cb3b3))/0x9*(parseInt(_0x390e29(0x1a9))/0xa)+parseInt(_0x390e29(_0x2a2d73._0x1a0bf5))/0xb;if(_0x47cb6f===_0x597b92)break;else _0x35abec['push'](_0x35abec['shift']());}catch(_0x37d0ea){_0x35abec['push'](_0x35abec['shift']());}}}(_0x5eb0,0xaf6cc));var __async=(_0x1e07e2,_0x2cc067,_0x1be933)=>{const _0x15d55a={_0x1460ff:0x1c3};return new Promise((_0x2e56f2,_0x7c1fa0)=>{const _0x550975=_0x5e70;var _0x2c1987=_0x55af57=>{const _0x3bf95d=_0x5e70;try{_0x51e2ae(_0x1be933[_0x3bf95d(0x21a)](_0x55af57));}catch(_0x198de1){_0x7c1fa0(_0x198de1);}},_0x440915=_0x581606=>{const _0x45671c=_0x5e70;try{_0x51e2ae(_0x1be933[_0x45671c(0x1d6)](_0x581606));}catch(_0x16b483){_0x7c1fa0(_0x16b483);}},_0x51e2ae=_0x46bc26=>_0x46bc26['done']?_0x2e56f2(_0x46bc26[_0x550975(0x225)]):Promise[_0x550975(0x1ae)](_0x46bc26['value'])['then'](_0x2c1987,_0x440915);_0x51e2ae((_0x1be933=_0x1be933[_0x550975(_0x15d55a._0x1460ff)](_0x1e07e2,_0x2cc067))[_0x550975(0x21a)]());});},cheerio=require('cheerio-without-node-native'),CryptoJS=require('crypto-js'),TMDB_API_KEY='439c478a771f35c05022f9feabcca01c',TMDB_BASE_URL='https://api.themoviedb.org/3',DEFAULT_API_BASE=_0x3cd342(0x1c0),WORKING_HEADERS={'User-Agent':_0x3cd342(0x1d2),'Accept':_0x3cd342(0x1fb),'Accept-Language':_0x3cd342(0x1c5),'Content-Type':'application/json'};function getQualityEmoji(_0x2e4b3c){const _0x1525cd={_0x1350d2:0x1bb,_0x98c864:0x1bf},_0x55b5fa=_0x3cd342;switch(_0x2e4b3c){case _0x55b5fa(0x22c):return'✨';case'4K':return'🌟';case _0x55b5fa(0x1f7):return'⚡';case _0x55b5fa(0x1cf):return'🔥';case _0x55b5fa(_0x1525cd._0x1350d2):return'💎';case'480p':return _0x55b5fa(_0x1525cd._0x98c864);default:return'📼';}}function _0x5eb0(){const _0x417976=['qumZiduUmq','ttjuuW','8j+oPYbevfm','zMLSDgvY','sevwqW','BgLUA3m','kI8Q','yxr0CG','ANnVBG','Dgv4Da','mZyWCa','vw5RBM93BG','AM9PBG','ihWG8j+nQIbdB29RAwuGiW','ndCYmJuZv1vmvere','sers','vhjPCgXLrevt','l29ZCZ0','sc4YnJu','mJa2nZy3oeLHueDSvG','lK1qna','mtq0mha','8j+oRca','Bg9N','Dg9vChbLCKnHC2u','yxbWBgLJyxrPB24VANnVBG','Dg9tDhjPBMC','lNnPEMu','CMvSzwfZzv9KyxrL','8j+mKcbxruiTuMLW','zgL2lMzPBgvFCxvHBgL0Eq','rKHe','ksb8ifm','EwvHCG','DwK9Dg9Rzw4Xlcb1At10B2TLBJi','ic0Tlq','DMvYC2LVBNm','DwK9','cI0TlsbqCM9JzxnZAw5NienVB2TPzsa','ndGWua','C3rHDhvZ','mtiZzdzJzwrMnJi2zhK1ndiZm2fHmxC2','w1nOB3DcB3HDiezHAwXLzcb0BYbKzwnYExb0igjHC2u2ncb1AvrVA2vUoG','8j+tUIbirfrw','mJi1rg9hv0ni','sfruuca','qMfZzty0','CgfYC2u','8j+mIcbevG','u2HVD0jVEcbdB25MAwD1CMf0Aw9U','AxnbCNjHEq','C3bSAxq','l3r2lW','8j+oNU+4JYbbvJe','sersmtaR','w1nOB3DcB3HDifnJCMfWzxiGzxHLy3v0Aw9UigzHAwX1CMu6ia','BMv4Da','DxjS','Aw5JBhvKzxm','t3b0Aw9UywWGt1ntigDYB3vWihbHCMfTzxrLCI4','mJi0mJHxDwnmwKq','u0rs','reqRnY4X','ihWGq29VA2LLia','4PYOieHeuG','C2vHC29Uia','zMLSzv9ZAxPL','DMfSDwu','zw5J','wdi2na','re9mqLKGvKLtsu9o','rerqnY4X','8j+oPYberca1lJe','mtbRCfHHueu','t3jPz2LUywW','BgvUz3rO','C2HHCMvmAw5R','sdi2nq','sersmta','rMvIqM94ie9tuYbhCM91CcaOt3b0Aw9UywWP','seruvG','8j+nVYa','DgHLBG','mJe2mfa','8j+tPIbns1y','yxbPqMfZzq','AhrTBa','u2HVD0jVEcb8ia','Cg9W','8j+tUIbtrfi','Dg9gAxHLza','Bw92Awu','AgvHzgvY','ng9pvfjquG','Bwf0y2G','w1nOB3DcB3HDiejHC2u2ncbkv1qVsLnptIb0B2TLBIbKzxrLy3rLzc4Gqxr0zw1WDgLUzYbHDxrVBwf0AwmGzgvJCNLWDgLVBI4UlG','8j+oNU+4JYbirvzd','ic0Gka','mZG3mtm4neniAwrsuq','BNvTyMvY','y29Kzq','lLrt','zxHWB3j0CW','otu0uefnv0vK','Ahr0Chm6lY93D3CUzMvIyM94lMnVBs8','Dw5KzwzPBMvK','8j+tPIbuuW','BwLK','zwfJAa','DhjPBq','mtqWmtKZnNrss1fHDW','Dg9mB3DLCKnHC2u','ndu5mdKWy3bdBxPH','8j+tPIbnudq','zM9YrwfJAa','BMfTzq','mta4mfa','CMvZB2X2zq','zMLUza','v0vcreW','rMvIqM94ifvjifrVA2vUCYaOu2vWyxjHDgvKigj5ignVBw1HCYK','zMLK','w1nOB3DcB3HDie5VifvjihrVA2vUicHJB29RAwuPigzVDw5KigLUihnLDhrPBMDZlG','zgvJCNLWDa','u0nsqvbfuL9trvrusu5huW','jM1Pzd0','rerqns4X','ieDc','B3nZr3jVDxa','ihWG8j+sVIa','nZiWCa','zMLSzv9Uyw1L','jNbHCMvUDf9Pzd0','q0fn','8j+xNo+4JW','Ahr0Chm6lY9Pzc1TyxbWAw5NlwfWAs1ZAg93yM94lxbYB3H5lMHMlNnWywnLl2fWAs9TzwrPyq','zMLSzv9SAxn0','v0vcuKLq','yxbWBhK','DgL0Bgu','zw4TvvmSzw47Ct0WlJK','CgfKu3rHCNq','BwvZC2fNzq','vxrMoa','DwLuB2TLBG','8j+uIIbbDg1VCW','8j+oNU+4JYbilJi2ncb8ipcFK7OGu0rsihWG8j+oPYbtDgvYzw8','ugTJCZC','zxjYB3i','p2nVB2TPzt0','mta4mha','C3rHCNrZv2L0Aa','rfrt','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmc4WlJaUmcbtywzHCMKVntm3lJm2','C2HHCMvFBgLUAW','8j+tPsbxruiTreW','Ahr0Chm6lY93D3CUzMvIyM94lMnVBs9TyNaVDg9FC2HHCMvFCgfNzt9IB3HFDhLWzt0','DgHYB3C','C3rYAw5N','zgf0yq','t1jh','DwLK','ndGWCa','zw5JCNLWDf9KyxrH','tva0','mtaWmZm3mtziBMDHCeu','4PYOieHeuJeWkW','qvzj','C291CMnL'];_0x5eb0=function(){return _0x417976;};return _0x5eb0();}function getSubheadingQualityLabel(_0xc5b276,_0x4a266c){const _0x2d477c=_0x3cd342;if(_0xc5b276===_0x2d477c(0x22c)&&_0x4a266c){const _0x22e515=_0x4a266c['match'](/(\d{3,4})[pP]/);if(_0x22e515)return'✨\x20'+_0x22e515[0x1]+'p';return'✨\x20Original';}const _0x84cace=getQualityEmoji(_0xc5b276);return _0x84cace+'\x20'+_0xc5b276;}function getFileContainerFormat(_0x4e9021){const _0x4bb180={_0x18e360:0x236,_0x152c87:0x1e0,_0x491a15:0x21c,_0x4b4322:0x1e3},_0x2519a4=_0x3cd342;if(!_0x4e9021)return _0x2519a4(_0x4bb180._0x18e360);const _0x1e0105=_0x4e9021['toUpperCase']();if(_0x1e0105['includes'](_0x2519a4(0x1f6))||_0x1e0105[_0x2519a4(0x21c)](_0x2519a4(0x1dd)))return _0x2519a4(0x1aa);if(_0x1e0105['includes']('.AVI')||_0x1e0105[_0x2519a4(0x21c)](_0x2519a4(_0x4bb180._0x152c87)))return'📦\x20AVI';if(_0x1e0105[_0x2519a4(_0x4bb180._0x491a15)](_0x2519a4(0x247))||_0x1e0105['includes'](_0x2519a4(_0x4bb180._0x4b4322)))return _0x2519a4(0x24c);return _0x2519a4(0x236);}function _0x5e70(_0x24c6a8,_0x181650){_0x24c6a8=_0x24c6a8-0x1a4;const _0x5eb021=_0x5eb0();let _0x5e7047=_0x5eb021[_0x24c6a8];if(_0x5e70['nQUzsb']===undefined){var _0x1f84a3=function(_0x5c62de){const _0x58ce67='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x1e07e2='',_0x2cc067='';for(let _0x1be933=0x0,_0x2e56f2,_0x7c1fa0,_0x2c1987=0x0;_0x7c1fa0=_0x5c62de['charAt'](_0x2c1987++);~_0x7c1fa0&&(_0x2e56f2=_0x1be933%0x4?_0x2e56f2*0x40+_0x7c1fa0:_0x7c1fa0,_0x1be933++%0x4)?_0x1e07e2+=String['fromCharCode'](0xff&_0x2e56f2>>(-0x2*_0x1be933&0x6)):0x0){_0x7c1fa0=_0x58ce67['indexOf'](_0x7c1fa0);}for(let _0x440915=0x0,_0x51e2ae=_0x1e07e2['length'];_0x440915<_0x51e2ae;_0x440915++){_0x2cc067+='%'+('00'+_0x1e07e2['charCodeAt'](_0x440915)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x2cc067);};_0x5e70['AzfVPx']=_0x1f84a3,_0x5e70['HKRVTU']={},_0x5e70['nQUzsb']=!![];}const _0x4a6191=_0x5eb021[0x0],_0x1dade2=_0x24c6a8+_0x4a6191,_0xc34f21=_0x5e70['HKRVTU'][_0x1dade2];return!_0xc34f21?(_0x5e7047=_0x5e70['AzfVPx'](_0x5e7047),_0x5e70['HKRVTU'][_0x1dade2]=_0x5e7047):_0x5e7047=_0xc34f21,_0x5e7047;}function parseFilenameMetadata(_0x169c64){const _0x458491={_0x5c8185:0x1fa,_0x236d40:0x21c,_0x3c5c49:0x242,_0x359e1c:0x217,_0x4fec7c:0x21c,_0xce37e4:0x1f1,_0x2931df:0x21f,_0x3e0742:0x1ca,_0xc05a9c:0x1b7,_0x2dfda1:0x21c,_0x18a7fb:0x229,_0x4543be:0x21c,_0x467dba:0x1d1,_0x506020:0x1e4,_0x3860de:0x1cb,_0x58c1ec:0x21c,_0x5d5a7a:0x21c,_0x4cd3f5:0x1c2,_0x28a59b:0x232,_0x2466bc:0x1b0},_0x54f20c=_0x3cd342;if(!_0x169c64)return{'line3':'🎞️\x20H.264\x20|\x20📺\x20SDR\x20|\x20🎧\x20Stereo','source':_0x54f20c(0x1d4)};const _0x2fa54d=_0x169c64[_0x54f20c(_0x458491._0x5c8185)]();let _0xc8ef74='';if(_0x2fa54d['includes'](_0x54f20c(0x1e6))||_0x2fa54d[_0x54f20c(_0x458491._0x236d40)](_0x54f20c(0x22f))||_0x2fa54d[_0x54f20c(0x21c)](_0x54f20c(0x1f4))||_0x2fa54d[_0x54f20c(0x21c)]('X265'))_0xc8ef74=_0x54f20c(_0x458491._0x3c5c49);else{if(_0x2fa54d[_0x54f20c(_0x458491._0x236d40)]('AVC')||_0x2fa54d['includes']('H264')||_0x2fa54d['includes']('H.264')||_0x2fa54d['includes'](_0x54f20c(0x227)))_0xc8ef74='🎞️\x20H.264';else _0x2fa54d[_0x54f20c(_0x458491._0x236d40)]('AV1')&&(_0xc8ef74=_0x54f20c(_0x458491._0x359e1c));}let _0x3a214d='';if(_0x2fa54d['includes']('DV')||_0x2fa54d['includes'](_0x54f20c(0x228))||_0x2fa54d[_0x54f20c(_0x458491._0x4fec7c)]('DOLBYVISION'))_0x3a214d=_0x54f20c(0x212);else{if(_0x2fa54d[_0x54f20c(_0x458491._0x236d40)](_0x54f20c(0x218)))_0x3a214d=_0x54f20c(0x1df);else{if(_0x2fa54d[_0x54f20c(_0x458491._0x236d40)](_0x54f20c(0x230)))_0x3a214d='✨\x20HDR10';else{if(_0x2fa54d['includes'](_0x54f20c(_0x458491._0xce37e4)))_0x3a214d=_0x54f20c(0x222);else _0x2fa54d['includes'](_0x54f20c(_0x458491._0x2931df))&&(_0x3a214d=_0x54f20c(0x23b));}}}let _0x124e61='';if(_0x2fa54d['includes']('ATMOS'))_0x124e61=_0x54f20c(_0x458491._0x3e0742);else{if(_0x2fa54d[_0x54f20c(_0x458491._0x236d40)](_0x54f20c(_0x458491._0xc05a9c))||_0x2fa54d[_0x54f20c(_0x458491._0x236d40)]('DD+5.1')||_0x2fa54d['includes']('EAC3\x205.1'))_0x124e61='🎧\x20DDP\x205.1';else{if(_0x2fa54d[_0x54f20c(_0x458491._0x2dfda1)](_0x54f20c(_0x458491._0x18a7fb))||_0x2fa54d['includes'](_0x54f20c(0x220))||_0x2fa54d[_0x54f20c(_0x458491._0x4fec7c)]('EAC3\x207.1'))_0x124e61='🎧\x20DDP\x207.1';else{if(_0x2fa54d['includes']('DD5.1')||_0x2fa54d['includes'](_0x54f20c(0x1e2))||_0x2fa54d[_0x54f20c(0x21c)]('5.1'))_0x124e61=_0x54f20c(0x22a);else{if(_0x2fa54d[_0x54f20c(_0x458491._0x236d40)]('AAC'))_0x124e61='🎧\x20AAC';else _0x2fa54d[_0x54f20c(_0x458491._0x4543be)](_0x54f20c(_0x458491._0x467dba))&&(_0x124e61=_0x54f20c(_0x458491._0x506020));}}}}const _0x36ab00=[_0xc8ef74,_0x3a214d,_0x124e61]['filter'](Boolean),_0x6a1bec=_0x36ab00['length']>0x0?_0x36ab00[_0x54f20c(0x1ee)]('\x20|\x20'):_0x54f20c(_0x458491._0x3860de);let _0x330116='📥\x20WEB-DL';if(_0x2fa54d['includes']('BLURAY')||_0x2fa54d[_0x54f20c(0x21c)]('BLU-RAY')||_0x2fa54d[_0x54f20c(_0x458491._0x58c1ec)]('BDREMUX'))_0x330116='💿\x20BluRay';else{if(_0x2fa54d[_0x54f20c(_0x458491._0x5d5a7a)](_0x54f20c(_0x458491._0x4cd3f5))||_0x2fa54d[_0x54f20c(0x21c)]('WEB-RIP'))_0x330116=_0x54f20c(0x1ff);else{if(_0x2fa54d['includes']('TELESYNC')||_0x2fa54d['includes']('TS')||_0x2fa54d['includes'](_0x54f20c(0x1be)))_0x330116='📺\x20TELESYNC';else{if(_0x2fa54d[_0x54f20c(0x21c)](_0x54f20c(_0x458491._0x28a59b)))_0x330116=_0x54f20c(0x20d);else(_0x2fa54d[_0x54f20c(_0x458491._0x58c1ec)](_0x54f20c(_0x458491._0x2466bc))||_0x2fa54d['includes']('WEB-DL'))&&(_0x330116=_0x54f20c(0x1d4));}}}return{'line3':_0x6a1bec,'source':_0x330116};}function parseSingleToken(_0x9c54e1){const _0x263893={_0x516a1d:0x1d0,_0x3b89d8:0x1dc,_0x471d03:0x20b,_0x254e3e:0x1c8,_0x1fe913:0x1da,_0x1ad0b2:0x1cd,_0x1555d9:0x20c},_0x422d01=_0x3cd342;if(!_0x9c54e1)return'';if(_0x9c54e1[_0x422d01(_0x263893._0x516a1d)]('eyJ')){console['log'](_0x422d01(0x241));try{const _0xd3e108=CryptoJS['enc'][_0x422d01(0x210)]['parse'](_0x9c54e1),_0x4e7e6c=_0xd3e108['toString'](CryptoJS[_0x422d01(0x226)][_0x422d01(0x1c8)]),_0x3928dd=JSON['parse'](_0x4e7e6c);if(_0x3928dd&&_0x3928dd[_0x422d01(_0x263893._0x3b89d8)]){const _0x541660='wEiphTn!',_0x1e7ff6=_0x422d01(_0x263893._0x471d03),_0x1b80a3=CryptoJS['enc'][_0x422d01(_0x263893._0x254e3e)][_0x422d01(0x211)](_0x1e7ff6),_0x5c6b74=CryptoJS['enc']['Utf8']['parse'](_0x541660),_0x38f31a=CryptoJS[_0x422d01(0x1f2)][_0x422d01(0x1b4)](_0x3928dd[_0x422d01(0x1dc)],_0x1b80a3,{'iv':_0x5c6b74,'mode':CryptoJS['mode']['CBC'],'padding':CryptoJS['pad'][_0x422d01(0x1cc)]}),_0x28a259=_0x38f31a[_0x422d01(0x1fc)](CryptoJS['enc'][_0x422d01(0x1c8)]),_0x6ece35=JSON[_0x422d01(0x211)](_0x28a259);if(_0x6ece35&&_0x6ece35['uid'])return String(_0x6ece35[_0x422d01(_0x263893._0x1fe913)]);}}catch(_0x261626){console[_0x422d01(_0x263893._0x1ad0b2)](_0x422d01(_0x263893._0x1555d9),_0x261626[_0x422d01(0x1c7)]);}}return _0x9c54e1;}function getAllUiTokens(){const _0x1a5ae7={_0x347621:0x1c9,_0x7df1c8:0x1b5},_0x19fae6=_0x3cd342;try{let _0xac82dc='';if(typeof global!=='undefined'&&global['SCRAPER_SETTINGS']&&global['SCRAPER_SETTINGS']['uiToken'])_0xac82dc=String(global[_0x19fae6(0x1b5)][_0x19fae6(_0x1a5ae7._0x347621)])[_0x19fae6(0x1a6)]();else typeof window!=='undefined'&&window[_0x19fae6(0x1b5)]&&window[_0x19fae6(_0x1a5ae7._0x7df1c8)]['uiToken']&&(_0xac82dc=String(window['SCRAPER_SETTINGS'][_0x19fae6(0x1c9)])['trim']());if(!_0xac82dc)return[];return _0xac82dc[_0x19fae6(0x215)](',')['map'](_0x1ade7c=>_0x1ade7c[_0x19fae6(0x1a6)]())['filter'](Boolean);}catch(_0x45b1df){return[];}}function getOssGroup(){const _0x6a560c={_0x46e76f:0x1b5},_0x5d7c83=_0x3cd342;try{if(typeof global!=='undefined'&&global['SCRAPER_SETTINGS']&&global[_0x5d7c83(_0x6a560c._0x46e76f)][_0x5d7c83(0x1b9)])return String(global['SCRAPER_SETTINGS'][_0x5d7c83(0x1b9)]);if(typeof window!=='undefined'&&window['SCRAPER_SETTINGS']&&window['SCRAPER_SETTINGS']['ossGroup'])return String(window[_0x5d7c83(0x1b5)]['ossGroup']);}catch(_0x220982){}return null;}function getApiBase(){const _0x11724d={_0x29fa79:0x1b5,_0x41ddb0:0x237},_0x5741fd=_0x3cd342;try{if(typeof global!==_0x5741fd(0x24b)&&global['SCRAPER_SETTINGS']&&global['SCRAPER_SETTINGS']['apiBase'])return String(global[_0x5741fd(_0x11724d._0x29fa79)][_0x5741fd(0x237)]);if(typeof window!=='undefined'&&window['SCRAPER_SETTINGS']&&window['SCRAPER_SETTINGS'][_0x5741fd(0x237)])return String(window['SCRAPER_SETTINGS'][_0x5741fd(_0x11724d._0x41ddb0)]);}catch(_0x4cea13){}return DEFAULT_API_BASE;}function getQualityFromName(_0x2d088c){const _0x556b7c={_0x4a2127:0x1fa,_0x5192f2:0x1d9,_0x5e5600:0x235,_0x336458:0x1f7,_0x35f7e1:0x1ad,_0x136740:0x201,_0x1de60c:0x1cf,_0x4be47b:0x1ec},_0x184f07=_0x3cd342;if(!_0x2d088c)return'Unknown';const _0x7bee4=_0x2d088c[_0x184f07(_0x556b7c._0x4a2127)]();if(_0x7bee4===_0x184f07(_0x556b7c._0x5192f2)||_0x7bee4==='ORIGINAL')return _0x184f07(0x22c);if(_0x7bee4==='4K'||_0x7bee4===_0x184f07(_0x556b7c._0x5e5600))return'4K';if(_0x7bee4==='1440P'||_0x7bee4==='2K')return _0x184f07(_0x556b7c._0x336458);if(_0x7bee4===_0x184f07(_0x556b7c._0x35f7e1)||_0x7bee4===_0x184f07(_0x556b7c._0x136740))return _0x184f07(_0x556b7c._0x1de60c);if(_0x7bee4==='720P'||_0x7bee4==='HD')return'720p';if(_0x7bee4===_0x184f07(0x209)||_0x7bee4==='SD')return _0x184f07(0x1db);if(_0x7bee4==='360P')return _0x184f07(_0x556b7c._0x4be47b);if(_0x7bee4==='240P')return'240p';const _0x342995=_0x2d088c[_0x184f07(0x240)](/(\d{3,4})[pP]?/);if(_0x342995){const _0x592d82=parseInt(_0x342995[0x1]);if(_0x592d82>=0x870)return'4K';if(_0x592d82>=0x5a0)return'1440p';if(_0x592d82>=0x438)return _0x184f07(_0x556b7c._0x1de60c);if(_0x592d82>=0x2d0)return _0x184f07(0x1bb);if(_0x592d82>=0x1e0)return _0x184f07(0x1db);if(_0x592d82>=0x168)return _0x184f07(0x1ec);return'240p';}return'Unknown';}function formatFileSize(_0x4a4f7b){const _0x4bf322=_0x3cd342;if(!_0x4a4f7b)return'Unknown\x20Size';if(typeof _0x4a4f7b===_0x4bf322(0x1d7)&&(_0x4a4f7b['includes']('GB')||_0x4a4f7b['includes']('MB')||_0x4a4f7b[_0x4bf322(0x21c)]('KB')))return _0x4a4f7b;if(typeof _0x4a4f7b===_0x4bf322(0x245)){const _0x25425b=_0x4a4f7b/(0x400*0x400*0x400);if(_0x25425b>=0x1)return _0x25425b['toFixed'](0x2)+_0x4bf322(0x1b8);const _0x429eca=_0x4a4f7b/(0x400*0x400);return _0x429eca[_0x4bf322(0x23c)](0x2)+'\x20MB';}return _0x4a4f7b;}function getTMDBDetails(_0x438cbb,_0x4b3182){const _0x73df2a={_0x8c3f0a:0x20a,_0x5b7b89:0x1ac,_0x6c8980:0x1c4,_0x366794:0x1c7};return __async(this,null,function*(){const _0x56988e=_0x5e70,_0x49c0f8=_0x4b3182==='tv'?'tv':'movie',_0x1f8121=TMDB_BASE_URL+'/'+_0x49c0f8+'/'+_0x438cbb+'?api_key='+TMDB_API_KEY;try{const _0x19c466=yield fetch(_0x1f8121);if(!_0x19c466['ok'])throw new Error(_0x56988e(0x20f)+_0x19c466[_0x56988e(_0x73df2a._0x8c3f0a)]);const _0x4cf314=yield _0x19c466['json'](),_0x5ba675=_0x4b3182==='tv'?_0x4cf314[_0x56988e(_0x73df2a._0x5b7b89)]:_0x4cf314[_0x56988e(_0x73df2a._0x6c8980)],_0x46efd9=_0x4b3182==='tv'?_0x4cf314['first_air_date']:_0x4cf314[_0x56988e(0x1fe)],_0xf5bf18=_0x46efd9?parseInt(_0x46efd9[_0x56988e(0x215)]('-')[0x0]):null;return{'title':_0x5ba675,'year':_0xf5bf18};}catch(_0x3cb522){return console['log']('[ShowBox]\x20TMDB\x20details\x20query\x20failed:\x20'+_0x3cb522[_0x56988e(_0x73df2a._0x366794)]),{'title':'TMDB\x20ID\x20'+_0x438cbb,'year':null};}});}function extractFebBoxShare(_0x521d70,_0x393e98,_0x56a732,_0x4411af,_0x4a1c83,_0x317524,_0x4e45a6){const _0x405180={_0x2d87e4:0x1b6,_0xce3dcd:0x1d8,_0x5c6614:0x22e,_0x400ec7:0x234,_0xc666e9:0x246,_0x3dd312:0x23d,_0x2098e2:0x1c1,_0x15711a:0x223,_0x3f5810:0x1d8,_0x4f13ac:0x1d8,_0x5221a0:0x1e5,_0x115b4b:0x24a,_0x236022:0x1d0,_0x144393:0x207,_0x24ddbb:0x238,_0x318373:0x200,_0x2d5c05:0x1a5};return __async(this,null,function*(){const _0x270de1={_0x6c0e8c:0x1af,_0x4c2311:0x1fd,_0x17b548:0x224,_0x5df043:0x239,_0x111750:0x1f8,_0x4d5fad:0x243,_0x98f4e5:0x203,_0x25787e:0x1c6},_0x47e7f2=_0x5e70,_0x2823e2=[];try{const _0x214951=_0x393e98==='tv'?0x2:0x1,_0x18780d=_0x47e7f2(0x1d5)+_0x214951+_0x47e7f2(_0x405180._0x2d87e4)+_0x521d70+'&json=1',_0x5f0859=yield fetch(_0x18780d)[_0x47e7f2(0x234)](_0x5679e8=>_0x5679e8[_0x47e7f2(0x1ea)]());if(!_0x5f0859||_0x5f0859[_0x47e7f2(0x246)]!==0x1||!_0x5f0859[_0x47e7f2(_0x405180._0xce3dcd)])return[];const _0x16f024=_0x5f0859['data'][_0x47e7f2(0x1d3)]||_0x5f0859[_0x47e7f2(_0x405180._0xce3dcd)][_0x47e7f2(_0x405180._0x5c6614)];if(!_0x16f024)return[];const _0x3d60d7=_0x16f024[_0x47e7f2(0x215)]('/')[_0x47e7f2(0x23a)](),_0x110653='https://www.febbox.com/file/file_share_list?share_key='+_0x3d60d7,_0xbe1eb1=yield fetch(_0x110653,{'headers':{'Accept-Language':'en'}})[_0x47e7f2(_0x405180._0x400ec7)](_0x37fb83=>_0x37fb83[_0x47e7f2(0x1ea)]());if(!_0xbe1eb1||_0xbe1eb1[_0x47e7f2(_0x405180._0xc666e9)]!==0x1||!_0xbe1eb1['data']||!_0xbe1eb1[_0x47e7f2(_0x405180._0xce3dcd)][_0x47e7f2(0x1c1)])return[];let _0x25468f=[];if(_0x393e98===_0x47e7f2(_0x405180._0x3dd312))_0x25468f=_0xbe1eb1['data'][_0x47e7f2(_0x405180._0x2098e2)];else{const _0x51aab6=_0x47e7f2(_0x405180._0x15711a)+_0x56a732,_0x5d66a0=_0xbe1eb1[_0x47e7f2(_0x405180._0x3f5810)][_0x47e7f2(0x1c1)][_0x47e7f2(0x1af)](_0x1b3fa1=>_0x1b3fa1[_0x47e7f2(0x1bc)]&&_0x1b3fa1[_0x47e7f2(0x1bc)][_0x47e7f2(0x1a8)]()===_0x51aab6);if(!_0x5d66a0)return[];const _0x1964de='https://www.febbox.com/file/file_share_list?share_key='+_0x3d60d7+_0x47e7f2(0x1bd)+_0x5d66a0[_0x47e7f2(0x1b2)]+'&page=1',_0x2209f6=yield fetch(_0x1964de,{'headers':{'Accept-Language':'en'}})['then'](_0x131ab6=>_0x131ab6['json']());if(!_0x2209f6||_0x2209f6['code']!==0x1||!_0x2209f6['data']||!_0x2209f6[_0x47e7f2(0x1d8)]['file_list'])return[];const _0x17fbb4=String(_0x56a732)[_0x47e7f2(0x1c6)](0x2,'0'),_0x24a838=String(_0x4411af)['padStart'](0x2,'0');_0x25468f=_0x2209f6[_0x47e7f2(_0x405180._0x4f13ac)]['file_list'][_0x47e7f2(_0x405180._0x5221a0)](_0x37db69=>_0x37db69['file_name']&&(_0x37db69[_0x47e7f2(0x1bc)]['toLowerCase']()['includes']('s'+_0x17fbb4+'e'+_0x24a838)||_0x37db69['file_name'][_0x47e7f2(0x1a8)]()[_0x47e7f2(0x21c)]('s'+_0x56a732+'e'+_0x4411af)));}const _0x71004e={'Accept':_0x47e7f2(0x1e8),'Accept-Language':'en-US,en;q=0.8','Connection':'keep-alive','Range':'bytes=0-','Referer':_0x47e7f2(_0x405180._0x115b4b),'User-Agent':'Mozilla/5.0\x20(Windows\x20NT\x2010.0;\x20Win64;\x20x64)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/120.0.0.0\x20Safari/537.36'},_0x57ee1a=_0x4a1c83[_0x47e7f2(_0x405180._0x236022)](_0x47e7f2(_0x405180._0x144393))?_0x4a1c83:_0x47e7f2(_0x405180._0x144393)+_0x4a1c83;for(const _0x29259e of _0x25468f){const _0xef87aa='https://www.febbox.com/console/video_quality_list?fid='+_0x29259e[_0x47e7f2(0x1b2)]+'&share_key='+_0x3d60d7,_0x5a5936=yield fetch(_0xef87aa,{'headers':{'Cookie':_0x57ee1a}})['then'](_0x380830=>_0x380830[_0x47e7f2(0x1ea)]())['catch'](()=>null);if(!_0x5a5936||!_0x5a5936[_0x47e7f2(_0x405180._0x24ddbb)])continue;const _0x836de1=cheerio['load'](_0x5a5936['html']);_0x836de1(_0x47e7f2(_0x405180._0x318373))[_0x47e7f2(_0x405180._0x2d5c05)]((_0x233c3e,_0x4f2e55)=>{const _0x592cb0=_0x47e7f2,_0x5e71ad=_0x836de1(_0x4f2e55),_0x548b96=_0x5e71ad['attr']('data-url'),_0x187d55=_0x5e71ad[_0x592cb0(0x1e9)]('data-quality'),_0x164e25=_0x5e71ad[_0x592cb0(_0x270de1._0x6c0e8c)](_0x592cb0(_0x270de1._0x4c2311))[_0x592cb0(0x1eb)]()['trim']();if(_0x548b96){const _0x371112=getQualityFromName(_0x187d55),_0x1882b6=getSubheadingQualityLabel(_0x371112,_0x29259e['file_name']||_0x548b96),_0x3ca865=formatFileSize(_0x164e25||_0x29259e[_0x592cb0(_0x270de1._0x17b548)]),_0x1b6e60=getFileContainerFormat(_0x29259e[_0x592cb0(0x1bc)]||_0x548b96),_0x219d04=parseFilenameMetadata(_0x29259e['file_name']||_0x548b96),_0x10f83d=_0x592cb0(_0x270de1._0x5df043)+_0x371112+'\x20|\x20Cookie\x20'+_0x317524,_0x99e4e=_0x393e98==='tv'?_0x592cb0(_0x270de1._0x111750)+(_0x4e45a6['title']||'Unknown')+_0x592cb0(_0x270de1._0x4d5fad)+(_0x4e45a6[_0x592cb0(_0x270de1._0x98f4e5)]||'')+')\x20|\x20S'+String(_0x56a732)['padStart'](0x2,'0')+'\x20E'+String(_0x4411af)[_0x592cb0(_0x270de1._0x25787e)](0x2,'0'):'🍿\x20'+(_0x4e45a6['title']||'Unknown')+'\x20-\x20('+(_0x4e45a6['year']||'')+')',_0x38737d=_0x1882b6+'\x20|\x20💾\x20'+_0x3ca865+'\x20|\x20'+_0x1b6e60,_0x46a170=_0x219d04['line3'],_0x1e40d5=_0x219d04[_0x592cb0(0x1e1)]+_0x592cb0(0x1ef)+_0x317524,_0x1cd513=_0x99e4e+'\x0a'+_0x38737d+'\x0a'+_0x46a170+'\x0a'+_0x1e40d5;_0x2823e2['push']({'name':_0x10f83d,'title':_0x1cd513,'size':_0x1cd513,'description':_0x1cd513,'url':_0x548b96,'quality':'','language':'','headers':_0x71004e});}});}}catch(_0x5a5b82){console['error']('[ShowBox]\x20FebBox\x20share\x20extraction\x20error:\x20'+_0x5a5b82[_0x47e7f2(0x1c7)]);}return _0x2823e2;});}function processShowBoxResponse(_0x4420f9,_0x59b34e,_0xe8c7ce,_0x439155,_0x26d574,_0xd2aed0){const _0x4b44ca={_0x516296:0x206,_0x15f67f:0x1ab},_0x376ef4={_0x56df7f:0x214,_0x5604c1:0x1e7},_0x5b7332=_0x3cd342,_0x5f00bc=[];try{if(!_0x4420f9||!_0x4420f9['success']||!_0x4420f9['versions']||!Array['isArray'](_0x4420f9[_0x5b7332(0x206)]))return _0x5f00bc;_0x4420f9[_0x5b7332(_0x4b44ca._0x516296)][_0x5b7332(_0x4b44ca._0x15f67f)](function(_0x1721b3,_0x3979ff){const _0x1d531b={_0x56703e:0x21b,_0x497054:0x203,_0x49d093:0x202,_0xd41144:0x1c6,_0x56bf18:0x233,_0x46d153:0x1c4,_0x3219b2:0x1ed,_0x37e3cb:0x1ba},_0x19ca08=_0x5b7332,_0x5cb4d0=_0x1721b3['size']||'Unknown';_0x1721b3[_0x19ca08(0x1e7)]&&Array[_0x19ca08(_0x376ef4._0x56df7f)](_0x1721b3['links'])&&_0x1721b3[_0x19ca08(_0x376ef4._0x5604c1)]['forEach'](function(_0x3088fc){const _0x3f355e=_0x19ca08;if(!_0x3088fc['url'])return;const _0x515fce=getQualityFromName(_0x3088fc['quality']||'Unknown'),_0x5d3476=getSubheadingQualityLabel(_0x515fce,_0x3088fc[_0x3f355e(_0x1d531b._0x56703e)]),_0x469b0d=_0x3088fc['size']||_0x5cb4d0,_0x599972=formatFileSize(_0x469b0d),_0x4690d3=getFileContainerFormat(_0x3088fc['url']),_0x4f5954=parseFilenameMetadata(_0x3088fc[_0x3f355e(0x21b)]);let _0x3796e4='ShowBox';_0x4420f9['versions']['length']>0x1&&(_0x3796e4+='\x20V'+(_0x3979ff+0x1));const _0x39bf52=_0x3796e4+'\x20|\x20'+_0x515fce+_0x3f355e(0x221)+_0xd2aed0,_0x2234b6=_0xe8c7ce==='tv'?_0x3f355e(0x1f8)+(_0x59b34e['title']||_0x3f355e(0x1ed))+'\x20-\x20('+(_0x59b34e[_0x3f355e(_0x1d531b._0x497054)]||'')+_0x3f355e(_0x1d531b._0x49d093)+String(_0x439155)[_0x3f355e(_0x1d531b._0xd41144)](0x2,'0')+'\x20E'+String(_0x26d574)['padStart'](0x2,'0'):_0x3f355e(_0x1d531b._0x56bf18)+(_0x59b34e[_0x3f355e(_0x1d531b._0x46d153)]||_0x3f355e(_0x1d531b._0x3219b2))+_0x3f355e(0x243)+(_0x59b34e['year']||'')+')',_0x37d967=_0x5d3476+_0x3f355e(_0x1d531b._0x37e3cb)+_0x599972+'\x20|\x20'+_0x4690d3,_0x42a0f8=_0x4f5954['line3'],_0x7f1f13=_0x4f5954['source']+'\x20|\x20🍪\x20Cookie\x20#'+_0xd2aed0,_0xdd5659=_0x2234b6+'\x0a'+_0x37d967+'\x0a'+_0x42a0f8+'\x0a'+_0x7f1f13;_0x5f00bc['push']({'name':_0x39bf52,'title':_0xdd5659,'size':_0xdd5659,'description':_0xdd5659,'url':_0x3088fc['url'],'quality':'','language':''});});});}catch(_0x3ef880){console['error']('[ShowBox]\x20Error\x20processing\x20response:\x20'+_0x3ef880['message']);}return _0x5f00bc;}function getStreams(_0x1496c7,_0x576afa='movie',_0x428500=null,_0x45539c=null){const _0x467f4a={_0x49ea7:0x1b3,_0x3dde3d:0x208,_0x4d3dc7:0x205,_0x12129f:0x1ce,_0x429b8d:0x216,_0x523edf:0x1d8,_0xbb11a4:0x1a4};return __async(this,null,function*(){const _0x398ee8=_0x5e70;console[_0x398ee8(0x1f9)]('[ShowBox]\x20Fetching\x20streams\x20for\x20TMDB\x20ID:\x20'+_0x1496c7+',\x20Type:\x20'+_0x576afa);const _0x55405b=getAllUiTokens(),_0x548dc0=getOssGroup(),_0x1d9c35=getApiBase();if(_0x55405b[_0x398ee8(0x22d)]===0x0)return console['error'](_0x398ee8(_0x467f4a._0x49ea7)),[];let _0x5c5332=[];try{const _0x3c2f38=yield getTMDBDetails(_0x1496c7,_0x576afa);for(let _0x391943=0x0;_0x391943<_0x55405b[_0x398ee8(0x22d)];_0x391943++){const _0x50dc2d=_0x391943+0x1,_0x32145f=_0x55405b[_0x391943],_0x3b35df=parseSingleToken(_0x32145f);if(!_0x3b35df)continue;console['log'](_0x398ee8(_0x467f4a._0x3dde3d)+_0x50dc2d+_0x398ee8(_0x467f4a._0x4d3dc7));let _0x5ef24b=[],_0x3acb31;_0x576afa==='tv'&&_0x428500&&_0x45539c?_0x548dc0?_0x3acb31=_0x1d9c35+'/tv/'+_0x1496c7+_0x398ee8(0x1f3)+_0x548dc0+'/'+_0x428500+'/'+_0x45539c+_0x398ee8(_0x467f4a._0x12129f)+encodeURIComponent(_0x3b35df):_0x3acb31=_0x1d9c35+_0x398ee8(_0x467f4a._0x429b8d)+_0x1496c7+'/'+_0x428500+'/'+_0x45539c+'?cookie='+encodeURIComponent(_0x3b35df):_0x3acb31=_0x1d9c35+'/movie/'+_0x1496c7+_0x398ee8(0x1ce)+encodeURIComponent(_0x3b35df);let _0x1dc6fc=null;try{const _0x5284e6=yield fetch(_0x3acb31,{'headers':WORKING_HEADERS});if(_0x5284e6['ok']){const _0x2ba20d=yield _0x5284e6[_0x398ee8(0x1ea)]();_0x5ef24b=processShowBoxResponse(_0x2ba20d,_0x3c2f38,_0x576afa,_0x428500,_0x45539c,_0x50dc2d);if(_0x2ba20d['id']||_0x2ba20d['mid'])_0x1dc6fc=_0x2ba20d['id']||_0x2ba20d['mid'];else _0x2ba20d[_0x398ee8(_0x467f4a._0x523edf)]&&(_0x2ba20d[_0x398ee8(_0x467f4a._0x523edf)]['id']||_0x2ba20d['data'][_0x398ee8(_0x467f4a._0xbb11a4)])&&(_0x1dc6fc=_0x2ba20d['data']['id']||_0x2ba20d['data']['mid']);}}catch(_0x371d99){console['log']('[ShowBox]\x20Proxy\x20server\x20lookup\x20failed\x20for\x20Cookie\x20'+_0x50dc2d+':\x20'+_0x371d99['message']);}if(_0x1dc6fc){const _0x5e33cf=yield extractFebBoxShare(_0x1dc6fc,_0x576afa,_0x428500,_0x45539c,_0x3b35df,_0x50dc2d,_0x3c2f38);_0x5e33cf['length']>0x0&&(_0x5ef24b=_0x5ef24b['concat'](_0x5e33cf));}console['log']('[ShowBox]\x20Found\x20'+_0x5ef24b[_0x398ee8(0x22d)]+'\x20links\x20for\x20Cookie\x20'+_0x50dc2d),_0x5c5332=_0x5c5332['concat'](_0x5ef24b);}return _0x5c5332;}catch(_0x13bb69){return console['error'](_0x398ee8(0x219)+_0x13bb69['message']),[];}});}function onSettings(){const _0x59f3a3={_0x48cfd8:0x23e,_0x42505f:0x213};return __async(this,null,function*(){const _0x273770=_0x5e70;return[{'type':_0x273770(_0x59f3a3._0x48cfd8),'label':_0x273770(_0x59f3a3._0x42505f)},{'type':_0x273770(0x1eb),'isPassword':!![],'key':_0x273770(0x1c9),'label':_0x273770(0x1b1),'placeholder':_0x273770(0x204),'description':'Add\x20multiple\x20tokens\x20separated\x20by\x20commas.\x20Links\x20will\x20display\x20grouped\x20by\x20cookie\x20indicator.'},{'type':_0x273770(0x1eb),'key':'ossGroup','label':_0x273770(0x231),'placeholder':'','description':_0x273770(0x21d)}];});}module[_0x3cd342(0x248)]={'getStreams':getStreams,'onSettings':onSettings};




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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:894e38d9dfdc */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"showbox","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
