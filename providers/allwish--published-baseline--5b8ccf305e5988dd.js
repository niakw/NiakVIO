const _0x2c2e6d=_0xf68e;(function(_0x4ca543,_0xddd23){const _0x5bb1b7=_0xf68e,_0x394889=_0x4ca543();while(!![]){try{const _0x3e0132=-parseInt(_0x5bb1b7(0x11f))/0x1+parseInt(_0x5bb1b7(0xb8))/0x2*(parseInt(_0x5bb1b7(0x150))/0x3)+-parseInt(_0x5bb1b7(0x14a))/0x4+parseInt(_0x5bb1b7(0xd0))/0x5*(-parseInt(_0x5bb1b7(0xba))/0x6)+parseInt(_0x5bb1b7(0x139))/0x7*(parseInt(_0x5bb1b7(0x13a))/0x8)+-parseInt(_0x5bb1b7(0xe4))/0x9*(-parseInt(_0x5bb1b7(0x111))/0xa)+-parseInt(_0x5bb1b7(0xf2))/0xb;if(_0x3e0132===_0xddd23)break;else _0x394889['push'](_0x394889['shift']());}catch(_0x55b124){_0x394889['push'](_0x394889['shift']());}}}(_0xc8f3,0xbd25a));var __defProp=Object[_0x2c2e6d(0xf8)],__defProps=Object['defineProperties'],__getOwnPropDescs=Object[_0x2c2e6d(0x104)],__getOwnPropSymbols=Object['getOwnPropertySymbols'],__hasOwnProp=Object[_0x2c2e6d(0xc9)][_0x2c2e6d(0xf5)],__propIsEnum=Object[_0x2c2e6d(0xc9)]['propertyIsEnumerable'],__defNormalProp=(_0xf040fc,_0x508bfd,_0xb4428b)=>_0x508bfd in _0xf040fc?__defProp(_0xf040fc,_0x508bfd,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0xb4428b}):_0xf040fc[_0x508bfd]=_0xb4428b,__spreadValues=(_0x195fe3,_0x36422a)=>{const _0x603060=_0x2c2e6d;for(var _0x2afa6d in _0x36422a||(_0x36422a={}))if(__hasOwnProp[_0x603060(0x120)](_0x36422a,_0x2afa6d))__defNormalProp(_0x195fe3,_0x2afa6d,_0x36422a[_0x2afa6d]);if(__getOwnPropSymbols)for(var _0x2afa6d of __getOwnPropSymbols(_0x36422a)){if(__propIsEnum[_0x603060(0x120)](_0x36422a,_0x2afa6d))__defNormalProp(_0x195fe3,_0x2afa6d,_0x36422a[_0x2afa6d]);}return _0x195fe3;},__spreadProps=(_0x340b78,_0xf3dbff)=>__defProps(_0x340b78,__getOwnPropDescs(_0xf3dbff)),__async=(_0x219ac4,_0x41e316,_0xe46133)=>{return new Promise((_0x466e92,_0x208718)=>{const _0x10d627=_0xf68e;var _0xafb8ed=_0x109bb2=>{const _0x57f0fe=_0xf68e;try{_0x2885fb(_0xe46133[_0x57f0fe(0x14c)](_0x109bb2));}catch(_0x251dae){_0x208718(_0x251dae);}},_0x40e3d4=_0x2e2e95=>{try{_0x2885fb(_0xe46133['throw'](_0x2e2e95));}catch(_0xd7854f){_0x208718(_0xd7854f);}},_0x2885fb=_0x39bb5e=>_0x39bb5e[_0x10d627(0xc0)]?_0x466e92(_0x39bb5e[_0x10d627(0xce)]):Promise[_0x10d627(0xf7)](_0x39bb5e[_0x10d627(0xce)])[_0x10d627(0xf0)](_0xafb8ed,_0x40e3d4);_0x2885fb((_0xe46133=_0xe46133[_0x10d627(0xe1)](_0x219ac4,_0x41e316))[_0x10d627(0x14c)]());});},cheerio=require(_0x2c2e6d(0xd8)),CryptoJS=require(_0x2c2e6d(0xcd)),PROVIDER_NAME=_0x2c2e6d(0xb6),MAIN_URL=_0x2c2e6d(0xe0),TMDB_API_KEY=_0x2c2e6d(0xca),REQUEST_TIMEOUT=0x2ee0,EPISODE_LIST_TIMEOUT=0x7530,VRF_SECRET='ysJhV6U27FVIjjuk',HEADERS={'User-Agent':_0x2c2e6d(0xd6),'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8','Accept-Language':_0x2c2e6d(0x14e),'Connection':'keep-alive'},AJAX_HEADERS={'X-Requested-With':_0x2c2e6d(0x122),'User-Agent':HEADERS[_0x2c2e6d(0xc4)],'Referer':MAIN_URL+'/'};function fetchSafe(_0x15767a){return __async(this,arguments,function*(_0x4eff9c,_0x133c67={},_0x1f22fb=REQUEST_TIMEOUT){const _0x2d55b7=_0xf68e;try{const _0x25091a=typeof AbortSignal!==_0x2d55b7(0x105)&&AbortSignal[_0x2d55b7(0x125)]?AbortSignal[_0x2d55b7(0x125)](_0x1f22fb):null,_0xb2382a=__spreadProps(__spreadValues({},_0x133c67),{'headers':__spreadValues(__spreadValues({},HEADERS),_0x133c67['headers']||{})});if(_0x25091a)_0xb2382a[_0x2d55b7(0xb4)]=_0x25091a;const _0x398ba0=yield fetch(_0x4eff9c,_0xb2382a);return _0x398ba0;}catch(_0x311219){return console[_0x2d55b7(0x141)]('['+PROVIDER_NAME+_0x2d55b7(0x15d)+(_0x4eff9c||'')['substring'](0x0,0x64)+_0x2d55b7(0x148)+_0x311219[_0x2d55b7(0x118)]),null;}});}function fetchJson(_0x2f2610){return __async(this,arguments,function*(_0x23b0a9,_0x2891d4={},_0xe7baa3){const _0x3af8e8=_0xf68e;try{const _0xbfebbd=yield fetchSafe(_0x23b0a9,_0x2891d4,_0xe7baa3);if(!_0xbfebbd||!_0xbfebbd['ok'])return null;return JSON['parse'](yield _0xbfebbd[_0x3af8e8(0x16b)]());}catch(_0xc6bce2){return console[_0x3af8e8(0x141)]('['+PROVIDER_NAME+_0x3af8e8(0xff)+(_0x23b0a9||'')['substring'](0x0,0x64)+_0x3af8e8(0x148)+_0xc6bce2['message']),null;}});}function fetchHtml(_0x4ba983){return __async(this,arguments,function*(_0x1c1995,_0x39dff0={}){const _0x5acee7=_0xf68e;try{const _0x220ea2=yield fetchSafe(_0x1c1995,_0x39dff0);if(!_0x220ea2||!_0x220ea2['ok'])return null;return cheerio[_0x5acee7(0x12c)](yield _0x220ea2[_0x5acee7(0x16b)]());}catch(_0x4f4772){return console[_0x5acee7(0x141)]('['+PROVIDER_NAME+']\x20fetchHtml:\x20'+(_0x1c1995||'')[_0x5acee7(0xfc)](0x0,0x64)+'\x20->\x20'+_0x4f4772[_0x5acee7(0x118)]),null;}});}function makeStream(_0x246b71,_0x3bde92,_0x2bc1c1,_0x2c99fc,_0x32fc65={},_0x590048){const _0x231fb6=_0x2c2e6d,_0x2c7d70={'name':PROVIDER_NAME+_0x231fb6(0x14d)+_0x246b71,'title':_0x3bde92||'','url':_0x2bc1c1||'','quality':_0x2c99fc||'HD','headers':__spreadValues({'User-Agent':HEADERS[_0x231fb6(0xc4)]},_0x32fc65||{})};return _0x590048&&Array[_0x231fb6(0x102)](_0x590048)&&_0x590048[_0x231fb6(0xbd)]>0x0&&(_0x2c7d70[_0x231fb6(0xd1)]=_0x590048),_0x2c7d70;}function buildStreamLabels(_0x3df22d,_0x35b9ed,_0x14d38d,_0x2df68b){const _0x547b87=_0x2c2e6d,_0x12e808=_0x35b9ed||'HD',_0xf356ee=_0x12e808+(_0x14d38d?'\x20'+_0x14d38d:'');let _0x5b58b1='';return _0x2df68b&&_0x2df68b[_0x547b87(0x152)]?_0x2df68b[_0x547b87(0x10f)]==='tv'&&_0x2df68b[_0x547b87(0x132)]!=null&&_0x2df68b[_0x547b87(0xf3)]!=null?_0x5b58b1=_0x2df68b[_0x547b87(0x152)]+'\x0aS'+_0x2df68b[_0x547b87(0x132)]+'\x20E'+_0x2df68b[_0x547b87(0xf3)]+_0x547b87(0xee)+_0x12e808+_0x547b87(0xfe):_0x5b58b1=_0x2df68b[_0x547b87(0x152)]+'\x0a'+_0x12e808+'\x20·\x20HLS':_0x5b58b1=_0x3df22d+(_0x14d38d?'\x20'+_0x14d38d:'')+'\x0a'+_0x12e808+_0x547b87(0xfe),_0x5b58b1+=_0x547b87(0x163),{'name':_0xf356ee,'title':_0x5b58b1};}function dedupe(_0x31838e){const _0x593d3d=_0x2c2e6d,_0x20b6f3=new Set();return(_0x31838e||[])[_0x593d3d(0x137)](_0x5eb7a7=>{const _0x5ac165=_0x593d3d;if(!_0x5eb7a7||!_0x5eb7a7['url']||_0x20b6f3['has'](_0x5eb7a7['url']))return![];return _0x20b6f3['add'](_0x5eb7a7[_0x5ac165(0xc3)]),!![];});}function getTMDBInfo(_0x523e8a,_0x416b94){return __async(this,null,function*(){const _0x5edb60=_0xf68e,_0x41131c=String(_0x523e8a||'')[_0x5edb60(0x12a)](),_0x4473d9=_0x41131c[_0x5edb60(0x12b)]('tt'),_0x369740=_0x416b94==='tv'||_0x416b94===_0x5edb60(0x10b)?'tv':'movie';try{if(_0x4473d9){const _0x52cc96=yield fetchJson(_0x5edb60(0x161)+_0x41131c+_0x5edb60(0xd5)+TMDB_API_KEY+_0x5edb60(0xbf)),_0x502ac2=_0x52cc96?_0x369740==='tv'?_0x52cc96[_0x5edb60(0x168)]:_0x52cc96[_0x5edb60(0x164)]:null;if(_0x502ac2&&_0x502ac2[_0x5edb60(0xbd)]>0x0){const _0x876064=_0x502ac2[0x0];return{'id':_0x876064['id'],'title':_0x369740==='tv'?_0x876064['name']:_0x876064['title'],'originalTitle':_0x369740==='tv'?_0x876064[_0x5edb60(0x143)]:_0x876064[_0x5edb60(0x167)],'year':(_0x876064[_0x5edb60(0x15f)]||_0x876064[_0x5edb60(0xe2)]||'')[_0x5edb60(0xc7)]('-')[0x0],'genres':_0x876064[_0x5edb60(0x117)]||[],'imdbId':_0x41131c};}return{'id':_0x41131c,'title':_0x41131c,'originalTitle':_0x41131c,'year':null,'genres':[],'imdbId':_0x41131c};}else{const _0x1854ed=yield fetchJson('https://api.themoviedb.org/3/'+_0x369740+'/'+_0x41131c+_0x5edb60(0xd5)+TMDB_API_KEY+_0x5edb60(0xcb));if(_0x1854ed)return{'id':_0x1854ed['id'],'title':_0x369740==='tv'?_0x1854ed[_0x5edb60(0xc6)]:_0x1854ed[_0x5edb60(0x152)],'originalTitle':_0x369740==='tv'?_0x1854ed[_0x5edb60(0x143)]:_0x1854ed[_0x5edb60(0x167)],'year':(_0x1854ed[_0x5edb60(0x15f)]||_0x1854ed[_0x5edb60(0xe2)]||'')['split']('-')[0x0],'genres':(_0x1854ed[_0x5edb60(0xf4)]||[])['map'](_0x2e3aec=>_0x2e3aec['id']),'imdbId':_0x1854ed[_0x5edb60(0x145)]||_0x1854ed[_0x5edb60(0x162)]&&_0x1854ed[_0x5edb60(0x162)]['imdb_id']||null};}}catch(_0x2316be){console[_0x5edb60(0x141)]('['+PROVIDER_NAME+_0x5edb60(0x155)+_0x2316be['message']);}return{'id':_0x41131c,'title':_0x41131c,'originalTitle':_0x41131c,'year':null,'genres':[],'imdbId':null};});}function cleanTitle(_0x545905){const _0x5c1a86=_0x2c2e6d;return String(_0x545905||'')[_0x5c1a86(0x15a)]()[_0x5c1a86(0xb1)](/[^a-z0-9\s]/g,'\x20')[_0x5c1a86(0xb1)](/\s+/g,'\x20')[_0x5c1a86(0x12a)]();}function tokenize(_0x5aaef7){const _0x3af422=_0x2c2e6d;return cleanTitle(_0x5aaef7)[_0x3af422(0xc7)]('\x20')[_0x3af422(0x137)](Boolean);}function scoreTitle(_0x5ac27f,_0x2031c5,_0x51e3fb,_0x19557d){const _0x1816d0=_0x2c2e6d,_0x164ee7=tokenize(_0x2031c5);if(!_0x164ee7[_0x1816d0(0xbd)])return 0x0;const _0x577656=new Set(tokenize(_0x5ac27f)),_0x1cc5bd=cleanTitle(_0x5ac27f),_0x540e1e=cleanTitle(_0x2031c5),_0x221b24=tokenize(_0x5ac27f);if(_0x1cc5bd===_0x540e1e)return 1.5;const _0x38251a=_0x1cc5bd[_0x1816d0(0xb1)](/\s+tv$/,'')[_0x1816d0(0xb1)](/\s+movie$/,'')['replace'](/\s+anime$/,'')[_0x1816d0(0xb1)](/\s+specials?$/,'')[_0x1816d0(0x12a)]();if(_0x38251a===_0x540e1e)return 1.4;let _0x5d2e9d=0x0;for(const _0x233736 of _0x164ee7){if(_0x577656[_0x1816d0(0x106)](_0x233736))_0x5d2e9d++;}let _0x27db1c=_0x5d2e9d/Math[_0x1816d0(0xed)](_0x164ee7['length'],0x1);if(_0x1cc5bd['startsWith'](_0x540e1e)){_0x27db1c+=0.3;const _0x179f6f=_0x221b24[_0x1816d0(0xbd)]-_0x164ee7[_0x1816d0(0xbd)];_0x179f6f>0x2&&(_0x27db1c-=Math['min'](_0x179f6f*0.1,0.4));const _0x12bcb0=['part',_0x1816d0(0x129),_0x1816d0(0x132),_0x1816d0(0x112),_0x1816d0(0x12d),'special',_0x1816d0(0x12f),_0x1816d0(0x159),_0x1816d0(0x123),'films',_0x1816d0(0xe7)],_0x929984=_0x221b24[_0x1816d0(0xb9)](_0x164ee7[_0x1816d0(0xbd)])['filter'](_0x4c4c16=>_0x12bcb0[_0x1816d0(0xe9)](_0x4c4c16))[_0x1816d0(0xbd)];if(_0x929984>0x0)_0x27db1c-=0.2;}else _0x164ee7[_0x1816d0(0xbd)]<=0x4&&_0x5d2e9d===_0x164ee7[_0x1816d0(0xbd)]&&(_0x27db1c-=0.4);if(_0x51e3fb){const _0x22c22f=/\b(19|20)\d{2}\b/,_0x5ac534=_0x1cc5bd[_0x1816d0(0x13b)](_0x22c22f);if(_0x5ac534&&Math[_0x1816d0(0x100)](parseInt(_0x5ac534[0x0])-parseInt(_0x51e3fb))<=0x1)_0x27db1c+=0.5;else{if(_0x5ac534){const _0x2edd5f=Math[_0x1816d0(0x100)](parseInt(_0x5ac534[0x0])-parseInt(_0x51e3fb));_0x27db1c-=Math[_0x1816d0(0x110)](_0x2edd5f*0.1,0.8);}}}if(_0x19557d&&Number(_0x19557d)>0x1){const _0x4de336=Number(_0x19557d),_0x45ebf1=_0x1cc5bd[_0x1816d0(0x13b)](new RegExp('\x5cb'+_0x4de336+_0x1816d0(0x10a)+_0x4de336+'|\x5cbpart\x5cs*'+_0x4de336,'i'));if(_0x45ebf1)_0x27db1c+=0.4;else{const _0x5b2feb=_0x1cc5bd[_0x1816d0(0x13b)](/\b(?:season|part)\s*\d+/i);!_0x5b2feb&&(_0x27db1c-=0.3);}}return Math['min'](_0x27db1c,0x2);}function searchAllWish(_0xcfe9eb,_0x4466f7,_0x5abccc,_0x37043e){return __async(this,null,function*(){const _0xfe3060=_0xf68e;try{const _0x12bc75=[];if(_0xcfe9eb)_0x12bc75[_0xfe3060(0x154)](_0xcfe9eb);if(_0x4466f7&&_0x4466f7!==_0xcfe9eb)_0x12bc75[_0xfe3060(0x154)](_0x4466f7);if(_0x37043e&&Number(_0x37043e)>0x1){const _0x450227=Number(_0x37043e);_0xcfe9eb&&(_0x12bc75[_0xfe3060(0x154)](_0xcfe9eb+'\x20'+_0x450227),_0x12bc75[_0xfe3060(0x154)](_0xcfe9eb+_0xfe3060(0x108)+_0x450227));}const _0x48b11c=[];for(const _0x298c4f of _0x12bc75){const _0x4f1184=yield fetchHtml(MAIN_URL+'/filter?keyword='+encodeURIComponent(_0x298c4f)+_0xfe3060(0x121));if(!_0x4f1184)continue;_0x4f1184(_0xfe3060(0xea))[_0xfe3060(0xeb)]((_0x488885,_0x3d3f72)=>{const _0x47ae3c=_0xfe3060,_0x615fd8=_0x4f1184(_0x3d3f72)['find'](_0x47ae3c(0xdd))[_0x47ae3c(0x16b)]()[_0x47ae3c(0x12a)](),_0x3ec04a=_0x4f1184(_0x3d3f72)['find'](_0x47ae3c(0xdd))['attr'](_0x47ae3c(0x127));if(_0x615fd8&&_0x3ec04a){const _0x2c56c2=_0x3ec04a['replace'](/\/ep-\d+\/?$/i,'');_0x48b11c['push']({'title':_0x615fd8,'watchUrl':_0x2c56c2,'query':_0x298c4f});}});if(_0x48b11c[_0xfe3060(0xbd)]>0x0)break;}if(_0x48b11c[_0xfe3060(0xbd)]===0x0)return null;let _0x285339=null,_0x4f2bf7=-0x1;for(const _0x128c8a of _0x48b11c){const _0xdf55be=scoreTitle(_0x128c8a['title'],_0xcfe9eb||'',_0x5abccc||null,_0x37043e),_0x4f1667=_0x4466f7?scoreTitle(_0x128c8a['title'],_0x4466f7,_0x5abccc||null,_0x37043e):0x0,_0x444d38=Math[_0xfe3060(0xed)](_0xdf55be,_0x4f1667);_0x444d38>_0x4f2bf7&&(_0x4f2bf7=_0x444d38,_0x285339=_0x128c8a);}if(_0x4f2bf7<0.3)return console[_0xfe3060(0xaf)]('['+PROVIDER_NAME+']\x20Title\x20match\x20score\x20too\x20low:\x20'+_0x4f2bf7),null;return console[_0xfe3060(0xaf)]('['+PROVIDER_NAME+']\x20Best\x20match:\x20\x22'+_0x285339[_0xfe3060(0x152)]+'\x22\x20score='+_0x4f2bf7['toFixed'](0x2)),_0x285339;}catch(_0x15088a){return console['error']('['+PROVIDER_NAME+']\x20Search\x20error:\x20'+_0x15088a['message']),null;}});}function _0xf68e(_0x4a0a32,_0x16cf48){_0x4a0a32=_0x4a0a32-0xaf;const _0xc8f35=_0xc8f3();let _0xf68ece=_0xc8f35[_0x4a0a32];if(_0xf68e['ajTpux']===undefined){var _0x37bb49=function(_0x2aae78){const _0x146320='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0xf040fc='',_0x508bfd='';for(let _0xb4428b=0x0,_0x195fe3,_0x36422a,_0x2afa6d=0x0;_0x36422a=_0x2aae78['charAt'](_0x2afa6d++);~_0x36422a&&(_0x195fe3=_0xb4428b%0x4?_0x195fe3*0x40+_0x36422a:_0x36422a,_0xb4428b++%0x4)?_0xf040fc+=String['fromCharCode'](0xff&_0x195fe3>>(-0x2*_0xb4428b&0x6)):0x0){_0x36422a=_0x146320['indexOf'](_0x36422a);}for(let _0x340b78=0x0,_0xf3dbff=_0xf040fc['length'];_0x340b78<_0xf3dbff;_0x340b78++){_0x508bfd+='%'+('00'+_0xf040fc['charCodeAt'](_0x340b78)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x508bfd);};_0xf68e['bHDnhD']=_0x37bb49,_0xf68e['uTitBd']={},_0xf68e['ajTpux']=!![];}const _0x36a987=_0xc8f35[0x0],_0x38cdcf=_0x4a0a32+_0x36a987,_0x43618b=_0xf68e['uTitBd'][_0x38cdcf];return!_0x43618b?(_0xf68ece=_0xf68e['bHDnhD'](_0xf68ece),_0xf68e['uTitBd'][_0x38cdcf]=_0xf68ece):_0xf68ece=_0x43618b,_0xf68ece;}function _0xc8f3(){const _0x496e78=['AxnbCNjHEq','zgL2lNnLCNzLCI10ExbL','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','Dw5KzwzPBMvK','AgfZ','i21Lz2fWBgf5lxbSyxLLCG','ihnLyxnVBIa','zMLSzq','kd86C3r8BMr8CMr8DgGPxhmRC2vHC29UFhnLyxnVBLXZkG','C2vYAwvZ','CgfYC2u','zgf0ys1Pzhm','q0jd','BwvKAwfuExbL','BwLU','mJi5mfnwvvLjuq','Bw92Awu','xsbfCgLZB2rLigXPC3qGzMfPBgvK','l2fQyxGVC2vYDMvYp2DLDd0','xsbszxr1CM5PBMCG','Dg9tDhjPBMC','z2vUCMvFAwrZ','BwvZC2fNzq','z2v0','zgf0ys10ExbL','Ahr0Chm6lY9TzwDHCgXHEs5IDxP6','Bw9Kzq','D2f0y2HvCMW','sc1tDwi','mJa2nty5y2Tqs2nr','y2fSBa','jNbHz2u9mq','we1mshr0CfjLCxvLC3q','zMLSBq','B3jPz2LUywXuAxrSzq','DgLTzw91Da','zMXHDa','AhjLzG','w0r1yL0','CgfYDhm','DhjPBq','C3rHCNrZv2L0Aa','Bg9Hza','Bw92AwvZ','jtiW','C3bLy2LHBhm','p3zYzJ0','zgf0ys1KDwi','C2vHC29U','zgL2lNnLCNzLCI1SAxn0id4GzgL2lNnLCNzLCG','CMvZDwX0','Ahr0Chm6lY9TzwDHCgXHEs5IDxP6lW','iIaO','zMLSDgvY','ifm9','n2vJt0jRDa','mtG5ntG5nLPvDMXKta','Bwf0y2G','zMLUza','zxHWB3j0CW','CxvHBgL0Eq','xsbszxnVBhzLzdOGiG','zhvI','zxjYB3i','xsbAzw4GzxjYB3i6ia','B3jPz2LUywXFBMfTzq','mta4mha','Aw1KyL9Pza','C2vJDgLVBLr5Cgu','xsbtzwXLy3rLzcbLCgLZB2rLihnSDwC9','ic0+ia','AgfZu3vI','ntu1mZeYz2vjuM1i','C29YDa','BMv4Da','ihWG','zw4TvvmSzw47Ct0WlJu','AgfZrhvI','mtG2ndC0DuDfvg94','tI9b','DgL0Bgu','vw5RBM93BG','ChvZAa','xsbuturcigvYCM9YoIa','C3vI','zgf0ys1Pza','l2fQyxGVC2vYDMvYl2XPC3q/C2vYDMvYCZ0','B3zH','Dg9mB3DLCKnHC2u','zgf0ys1SAw5RlwLK','EwvHCG','xsbMzxrJAfnHzMu6ia','quvt','zMLYC3rFywLYx2rHDgu','jMLKpq','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY9MAw5KlW','zxH0zxjUywXFAwrZ','cMj5ihbPCMf0zxPVCM85','Bw92AwvFCMvZDwX0CW','xsboBYbZAg93ieLeigzVDw5K','BgfIzwW','B3jPz2LUywXFDgL0Bgu','DhzFCMvZDwX0CW','ieu9','BgfUz3vHz2u','Dgv4Da','Bg9N','igLKCZ0','CMvWBgfJzq','xsboBYbuturcigrHDge','xsbgyxrHBdOG','C2LNBMfS','ksWGCMvQzwn0Aw5N','qwXSv2LZAa','l2fQyxGVzxbPC29Kzs9SAxn0lW','mZrVyKTTBgy','C2XPy2u','nNfLEgzwAW','zNjVBq','ihn0CMvHBxm','BgvUz3rO','Ahr0Chm6lY9TzwDHCgXHEs5IDxP6l3n0CMvHBs9NzxrtB3vYy2vZp2LKpq','jMv4DgvYBMfSx3nVDxjJzt1PBwrIx2LK','zg9Uzq','zNjVBunOyxjdB2rL','C291CMnLCW','DxjS','vxnLCI1bz2vUDa','zgvJCNLWDa','BMfTzq','C3bSAxq','ugTJCZC','ChjVDg90ExbL','ndm5yZq3oge3nZfMmZvJmduWmJjMowzLywjJy2eWmwm','jMfWCgvUzf90B19YzxnWB25Zzt1LEhrLCM5HBf9Pzhm','zgL2lNjHBMDLid4GzgL2id4Gyq','y3j5ChrVlwPZ','DMfSDwu','xsboB3qGyw5PBwuGkgDLBNjLCZOG','mtu5mZaZnuneCeTWBW','C3vIDgL0BgvZ','zgf0ys1TywW','C2X1zW','vxrMoa','p2fWAv9RzxK9','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeZms4WlJaUmcbtywzHCMKVntm3lJm2','BwfW','y2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzL','zw5J','AM9PBG','xsbnzwDHugXHEsbLCNjVCJOG','qMfZzty0','zgL2lM5HBwuGpIbH','xsboBYbTyxrJAcbVBIbbBgXxAxnO','w0HHCMqGu3vIxq','Ahr0Chm6lY9HBgWTD2LZAc5Tzq','yxbWBhK','CMvSzwfZzv9KyxrL','Ahr0Chm6lY9WBgf5zxiUC2DZz3nNC3iUC2L0zs8','nJaZodfsDK1PueK','y2HHCKnVzgvbDa','DgvZDa','DgHL','zMLYC3q','Aw5JBhvKzxm','zgL2lML0zw0','zwfJAa','ywXS','Bwf4','imk3ia','A2LUza','DgHLBG','yxr0CG','mtuZmdqXmJr4CMrss04','zxbPC29Kzq','z2vUCMvZ','AgfZt3DUuhjVCgvYDhK','C3bHBG','CMvZB2X2zq','zgvMAw5LuhjVCgvYDhK','z2v0u3rYzwfTCW','w1n1yL0','CgfK','C3vIC3rYAw5N','xsbtzxj2zxiGCMvZB2X2zsbLCNjVCJOG','imk3ieHmuW','xsbMzxrJAePZB246ia','ywjZ','zgf0ys1ZDwi'];_0xc8f3=function(){return _0x496e78;};return _0xc8f3();}function generateEpisodeVrf(_0x500214){const _0xbed82f=_0x2c2e6d,_0x3cf55b=encodeURIComponent(_0x500214)[_0xbed82f(0xb1)](/%21/g,'!')[_0xbed82f(0xb1)](/%27/g,'\x27')['replace'](/%28/g,'(')[_0xbed82f(0xb1)](/%29/g,')')[_0xbed82f(0xb1)](/%7E/g,'~')[_0xbed82f(0xb1)](/%2A/g,'*')[_0xbed82f(0xb1)](/%20/g,_0xbed82f(0x12e)),_0x5087b8=Array['from'](VRF_SECRET)[_0xbed82f(0xd7)](_0x2d8d67=>_0x2d8d67[_0xbed82f(0xe5)](0x0)),_0x5c0b22=Array[_0xbed82f(0xbb)](_0x3cf55b)[_0xbed82f(0xd7)](_0x2f55e2=>_0x2f55e2[_0xbed82f(0xe5)](0x0)),_0x7caec5=Array[_0xbed82f(0xbb)]({'length':0x100},(_0x59ecf9,_0x2d9a50)=>_0x2d9a50);let _0x2ea21d=0x0;for(let _0x4e714d=0x0;_0x4e714d<=0xff;_0x4e714d++){_0x2ea21d=(_0x2ea21d+_0x7caec5[_0x4e714d]+_0x5087b8[_0x4e714d%_0x5087b8[_0xbed82f(0xbd)]])%0x100,[_0x7caec5[_0x4e714d],_0x7caec5[_0x2ea21d]]=[_0x7caec5[_0x2ea21d],_0x7caec5[_0x4e714d]];}const _0x4527aa=[];let _0xd982fb=0x0;_0x2ea21d=0x0;for(let _0x2ad2d8=0x0;_0x2ad2d8<_0x5c0b22['length'];_0x2ad2d8++){_0xd982fb=(_0xd982fb+0x1)%0x100,_0x2ea21d=(_0x2ea21d+_0x7caec5[_0xd982fb])%0x100,[_0x7caec5[_0xd982fb],_0x7caec5[_0x2ea21d]]=[_0x7caec5[_0x2ea21d],_0x7caec5[_0xd982fb]];const _0x11dff5=_0x7caec5[(_0x7caec5[_0xd982fb]+_0x7caec5[_0x2ea21d])%0x100];_0x4527aa[_0xbed82f(0x154)]((_0x5c0b22[_0x2ad2d8]^_0x11dff5)&0xff);}function _0x2eb1b3(_0x3e39b4){const _0x166389=_0xbed82f;let _0x1bc6de='';for(const _0x44dc53 of _0x3e39b4)_0x1bc6de+=String[_0x166389(0xc1)](_0x44dc53);return btoa(_0x1bc6de)[_0x166389(0xb1)](/\+/g,'-')['replace'](/\//g,'_')[_0x166389(0xb1)](/=+$/,'');}const _0xf4ec51=_0x2eb1b3(_0x4527aa),_0x2e33b5={0x0:-0x3,0x1:0x3,0x2:-0x4,0x3:0x2,0x4:-0x2,0x5:0x5,0x6:0x4,0x7:0x5},_0x7602ab=Array[_0xbed82f(0xbb)](_0xf4ec51)[_0xbed82f(0xd7)]((_0x11995f,_0x14904d)=>{const _0x33acd6=_0xbed82f;let _0x33bdb9=_0x11995f[_0x33acd6(0xe5)](0x0);return _0x33bdb9+=_0x2e33b5[_0x14904d%0x8]||0x0,_0x33bdb9&0xff;}),_0x3beaf3=_0x2eb1b3(_0x7602ab),_0x48d4ed=_0x11f4f3=>{const _0x4d4a03=_0xbed82f;if(_0x11f4f3>='A'&&_0x11f4f3<='Z')return String[_0x4d4a03(0xc1)]((_0x11f4f3['charCodeAt'](0x0)-0x41+0xd)%0x1a+0x41);if(_0x11f4f3>='a'&&_0x11f4f3<='z')return String['fromCharCode']((_0x11f4f3[_0x4d4a03(0xe5)](0x0)-0x61+0xd)%0x1a+0x61);return _0x11f4f3;};return Array[_0xbed82f(0xbb)](_0x3beaf3)[_0xbed82f(0xd7)](_0x48d4ed)[_0xbed82f(0xda)]('');}function chooseEpisode(_0x4a666d,_0x86455f,_0x4cb2f9,_0x20af93){const _0x509d1a=_0x2c2e6d,_0x21189a=_0x4a666d(_0x509d1a(0xcc))[_0x509d1a(0xd7)]((_0x400f86,_0x361b54)=>({'slug':parseInt(_0x4a666d(_0x361b54)['attr']('data-slug')||'0',0xa),'ids':_0x4a666d(_0x361b54)[_0x509d1a(0xf1)](_0x509d1a(0x10d))||'','hasSub':_0x4a666d(_0x361b54)[_0x509d1a(0xf1)](_0x509d1a(0x101))==='1','hasDub':_0x4a666d(_0x361b54)[_0x509d1a(0xf1)](_0x509d1a(0x131))==='1','malId':_0x4a666d(_0x361b54)[_0x509d1a(0xf1)]('data-mal')?parseInt(_0x4a666d(_0x361b54)['attr'](_0x509d1a(0xd2)),0xa):null}))[_0x509d1a(0x119)]()['filter'](_0x542e9e=>_0x542e9e['ids']);if(!_0x21189a['length'])return null;if(_0x20af93===_0x509d1a(0x112)||_0x4cb2f9==null)return _0x21189a[0x0];const _0x59e568=Number(_0x4cb2f9);return _0x21189a[_0x509d1a(0x13c)](_0x84cfa4=>_0x84cfa4[_0x509d1a(0xd3)]===_0x59e568)||null;}function extractMegaPlay(_0x122ebf,_0x4f95d5,_0x39d6a5){return __async(this,null,function*(){const _0x3adb51=_0xf68e;try{const _0x4e91f8=yield fetchSafe(_0x122ebf,{'headers':__spreadProps(__spreadValues({},HEADERS),{'X-Requested-With':'XMLHttpRequest','Referer':'https://megaplay.buzz/'})});if(!_0x4e91f8)return[];const _0x6d1a54=cheerio[_0x3adb51(0x12c)](yield _0x4e91f8[_0x3adb51(0x16b)]()),_0x5645d5=_0x6d1a54(_0x3adb51(0x107))[_0x3adb51(0xf1)](_0x3adb51(0x157));if(!_0x5645d5)return[];const _0x1a0258=yield fetchJson(_0x3adb51(0xbe)+_0x5645d5+_0x3adb51(0x160)+_0x5645d5,{'headers':__spreadProps(__spreadValues({},HEADERS),{'X-Requested-With':_0x3adb51(0x122),'Referer':_0x3adb51(0x135)})});if(!_0x1a0258||!_0x1a0258[_0x3adb51(0xc2)]||!_0x1a0258[_0x3adb51(0xc2)][_0x3adb51(0x109)])return[];const _0x3b0f5b=(_0x1a0258['tracks']||[])['filter'](_0x461d13=>_0x461d13['kind']==='captions'||_0x461d13[_0x3adb51(0xef)]===_0x3adb51(0xd1))[_0x3adb51(0xd7)](_0x284a1e=>({'label':_0x284a1e[_0x3adb51(0x166)]||_0x3adb51(0x153),'url':_0x284a1e[_0x3adb51(0x109)]}))[_0x3adb51(0x137)](_0x3369a8=>_0x3369a8[_0x3adb51(0xc3)]),_0x48a5ab=buildStreamLabels('MegaPlay',_0x3adb51(0x144),_0x4f95d5,_0x39d6a5);return[makeStream(_0x48a5ab[_0x3adb51(0xc6)],_0x48a5ab[_0x3adb51(0x152)],_0x1a0258[_0x3adb51(0xc2)][_0x3adb51(0x109)],'1080p',{'Referer':_0x3adb51(0x135),'Origin':_0x3adb51(0x11b),'User-Agent':HEADERS['User-Agent']},_0x3b0f5b[_0x3adb51(0xbd)]>0x0?_0x3b0f5b:void 0x0)];}catch(_0x2ef7ac){return console['error']('['+PROVIDER_NAME+_0x3adb51(0xdb)+_0x2ef7ac['message']),[];}});}function extractZen(_0x5d78a6,_0x33d978,_0x56adb3){return __async(this,null,function*(){const _0x11d295=_0xf68e;try{const _0x37de36=yield fetchSafe(_0x5d78a6,{'headers':HEADERS});if(!_0x37de36)return[];const _0x2cde77=yield _0x37de36[_0x11d295(0x16b)](),_0x267dd3=_0x2cde77[_0x11d295(0x13b)](/video_b64:\s*"([^"]+)"/),_0x4990a6=_0x2cde77[_0x11d295(0x13b)](/enc_key_b64:\s*"([^"]+)"/),_0x1ad258=_0x2cde77[_0x11d295(0x13b)](/iv_b64:\s*"([^"]+)"/),_0x5f3fd8=_0x2cde77[_0x11d295(0x13b)](/subtitles:\s*"([^"]*)"/);if(!_0x267dd3||!_0x4990a6||!_0x1ad258)return[];const _0x4087e8=_0x267dd3[0x1],_0x5a3e9b=_0x4990a6[0x1],_0x12dba7=_0x1ad258[0x1],_0x2cbb74=CryptoJS[_0x11d295(0xd9)]['Base64'][_0x11d295(0x10c)](_0x5a3e9b),_0x514354=CryptoJS[_0x11d295(0xd9)][_0x11d295(0xdc)]['parse'](_0x12dba7),_0x1d3aa9=CryptoJS[_0x11d295(0xd9)][_0x11d295(0xdc)]['parse'](_0x4087e8),_0x13bc80=CryptoJS[_0x11d295(0x15e)][_0x11d295(0xc5)]({'ciphertext':_0x1d3aa9},_0x2cbb74,{'iv':_0x514354,'mode':CryptoJS[_0x11d295(0x11c)][_0x11d295(0x10e)],'padding':CryptoJS[_0x11d295(0xfb)][_0x11d295(0xc8)]}),_0x3e33ec=_0x13bc80[_0x11d295(0x116)](CryptoJS['enc'][_0x11d295(0xd4)]);if(!_0x3e33ec)return[];let _0x40c735=[];if(_0x5f3fd8&&_0x5f3fd8[0x1])try{const _0xada49a=_0x5f3fd8[0x1][_0x11d295(0xb1)](/\\"/g,'\x22')[_0x11d295(0xb1)](/\\\\\//g,'/')[_0x11d295(0xb1)](/\\u([0-9a-fA-F]{4})/g,(_0x2973d5,_0x3a2a95)=>String[_0x11d295(0xc1)](parseInt(_0x3a2a95,0x10))),_0x3930df=JSON[_0x11d295(0x10c)](_0xada49a);Array['isArray'](_0x3930df)&&(_0x40c735=_0x3930df['filter'](_0x373e47=>_0x373e47[_0x11d295(0xc3)])['map'](_0x4d1eaa=>({'label':_0x4d1eaa[_0x11d295(0x16a)]||_0x11d295(0x153),'url':_0x4d1eaa[_0x11d295(0xc3)]})));}catch(_0x58cabb){}const _0x486464=buildStreamLabels('Zen',_0x11d295(0x144),_0x33d978,_0x56adb3);return[makeStream(_0x486464[_0x11d295(0xc6)],_0x486464[_0x11d295(0x152)],_0x3e33ec[_0x11d295(0x12a)](),_0x11d295(0x144),{'Referer':_0x11d295(0xe3),'Origin':_0x11d295(0xe3)},_0x40c735['length']>0x0?_0x40c735:void 0x0)];}catch(_0x355be7){return console[_0x11d295(0x141)]('['+PROVIDER_NAME+_0x11d295(0x142)+_0x355be7[_0x11d295(0x118)]),[];}});}function resolveServers(_0x579215,_0x5903f8,_0x26bd69){return __async(this,null,function*(){const _0x130670=_0xf68e;try{const _0x3c430d=yield fetchJson(MAIN_URL+_0x130670(0x158)+encodeURIComponent(_0x579215),{'headers':AJAX_HEADERS});if(!_0x3c430d||_0x3c430d['status']!==0xc8)return[];const _0x2da6c9=cheerio[_0x130670(0x12c)](_0x3c430d[_0x130670(0x134)]||''),_0x7d2569=[];_0x2da6c9(_0x130670(0x103))[_0x130670(0xeb)]((_0x33d671,_0x30df53)=>{const _0x340340=_0x130670,_0xa6f7b9=_0x2da6c9(_0x30df53)['attr'](_0x340340(0x11a)),_0x5b68e6=(_0x2da6c9(_0x30df53)[_0x340340(0x13c)](_0x340340(0xf6))[_0x340340(0xe8)]()[_0x340340(0x16b)]()||'')[_0x340340(0xe9)](_0x340340(0x11e));if(!_0x5903f8['includes'](_0xa6f7b9))return;_0x2da6c9(_0x30df53)[_0x340340(0x13c)](_0x340340(0x133))[_0x340340(0xeb)]((_0x2264aa,_0x3a6574)=>{const _0x146adb=_0x340340,_0xcde100=_0x2da6c9(_0x3a6574)['attr'](_0x146adb(0x15b));if(!_0xcde100)return;_0x7d2569[_0x146adb(0x154)]({'dataId':_0xcde100,'sectionType':_0xa6f7b9,'isHardSub':_0x5b68e6});});});if(_0x7d2569[_0x130670(0xbd)]===0x0)return[];const _0xf4e4b4=yield Promise[_0x130670(0xec)](_0x7d2569[_0x130670(0xd7)](_0x426d55=>__async(this,null,function*(){const _0x4d4419=_0x130670;try{const _0x117348=yield fetchJson(MAIN_URL+_0x4d4419(0x114)+encodeURIComponent(_0x426d55['dataId']),{'headers':AJAX_HEADERS});if(!_0x117348||!_0x117348['result']||!_0x117348[_0x4d4419(0x134)]['url'])return[];const _0x14f09b=_0x117348[_0x4d4419(0x134)][_0x4d4419(0xc3)],_0x62a8e1=_0x426d55[_0x4d4419(0x146)]===_0x4d4419(0x140)?_0x4d4419(0x128):_0x426d55['isHardSub']?_0x4d4419(0xdf):_0x4d4419(0xfa);if(/megaplay\.buzz/i['test'](_0x14f09b))return extractMegaPlay(_0x14f09b,_0x62a8e1,_0x26bd69);else{if(/player\.sgsgsgsr\.site|zencloudz\.cc/i['test'](_0x14f09b))return extractZen(_0x14f09b,_0x62a8e1,_0x26bd69);else{if(/vidwish\.live/i[_0x4d4419(0xe6)](_0x14f09b))return extractMegaPlay(_0x14f09b,_0x62a8e1,_0x26bd69);}}return[];}catch(_0x565754){return[];}})));return dedupe(_0xf4e4b4[_0x130670(0x126)]());}catch(_0x5828e0){return console[_0x130670(0x141)]('['+PROVIDER_NAME+_0x130670(0xfd)+_0x5828e0[_0x130670(0x118)]),[];}});}function getStreams(_0x2132d3,_0x54bdd0,_0x355997,_0x33819d){return __async(this,null,function*(){const _0xde36f2=_0xf68e;try{console['log']('['+PROVIDER_NAME+']\x20Request:\x20ID='+_0x2132d3+'\x20Type='+_0x54bdd0+_0xde36f2(0x138)+_0x355997+_0xde36f2(0x169)+_0x33819d);if(_0x54bdd0!=='tv'&&_0x54bdd0!==_0xde36f2(0x112))return[];const _0xdc407f=yield getTMDBInfo(_0x2132d3,_0x54bdd0);if(!_0xdc407f||!_0xdc407f[_0xde36f2(0x152)])return console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+_0xde36f2(0xb2)),[];console['log']('['+PROVIDER_NAME+_0xde36f2(0x13f)+_0xdc407f['title']+_0xde36f2(0x136)+(_0xdc407f[_0xde36f2(0x15c)]||_0xde36f2(0x151))+')');if(_0xdc407f[_0xde36f2(0xf4)]&&_0xdc407f[_0xde36f2(0xf4)][_0xde36f2(0xbd)]>0x0&&!_0xdc407f[_0xde36f2(0xf4)]['includes'](0x10))return console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+_0xde36f2(0xcf)+_0xdc407f[_0xde36f2(0xf4)]['join'](',')+_0xde36f2(0xb5)),[];const _0xe095c0=yield searchAllWish(_0xdc407f[_0xde36f2(0x152)],_0xdc407f[_0xde36f2(0x124)],_0xdc407f[_0xde36f2(0x15c)],_0x355997);if(!_0xe095c0||!_0xe095c0[_0xde36f2(0x11d)])return console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+_0xde36f2(0xde)),[];const _0x38038b=yield fetchHtml(_0xe095c0[_0xde36f2(0x11d)]);if(!_0x38038b)return[];const _0x327624=_0x38038b('main\x20>\x20div.container')[_0xde36f2(0xf1)](_0xde36f2(0x157));if(!_0x327624)return console['log']('['+PROVIDER_NAME+_0xde36f2(0x165)),[];const _0x1d6799=generateEpisodeVrf(_0x327624),_0x31fa2e=yield fetchJson(MAIN_URL+_0xde36f2(0xb7)+_0x327624+_0xde36f2(0x130)+encodeURIComponent(_0x1d6799),{'headers':AJAX_HEADERS},EPISODE_LIST_TIMEOUT);if(!_0x31fa2e||_0x31fa2e['status']!==0xc8)return console['log']('['+PROVIDER_NAME+_0xde36f2(0x113)),[];const _0x302b90=cheerio['load'](_0x31fa2e[_0xde36f2(0x134)]||''),_0x2b4615=_0x33819d!=null?Number(_0x33819d):null,_0x11a3f0=chooseEpisode(_0x302b90,_0x355997,_0x2b4615,_0x54bdd0);if(!_0x11a3f0)return console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+']\x20Episode\x20not\x20found\x20(looking\x20for\x20ep\x20'+_0x2b4615+')'),[];console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+_0xde36f2(0x147)+_0x11a3f0[_0xde36f2(0xd3)]+_0xde36f2(0xb0)+_0x11a3f0['ids'][_0xde36f2(0xfc)](0x0,0x1e)+'...');const _0x662c6b=[];if(_0x11a3f0[_0xde36f2(0x149)])_0x662c6b[_0xde36f2(0x154)](_0xde36f2(0x156));if(_0x11a3f0[_0xde36f2(0x14f)])_0x662c6b[_0xde36f2(0x154)]('dub');if(_0x662c6b[_0xde36f2(0xbd)]===0x0)return[];const _0x2d95c7={'title':_0xdc407f[_0xde36f2(0x152)],'season':_0x355997,'episode':_0x33819d,'mediaType':_0x54bdd0},_0x33b2e0=yield resolveServers(_0x11a3f0['ids'],_0x662c6b,_0x2d95c7);console[_0xde36f2(0xaf)]('['+PROVIDER_NAME+_0xde36f2(0x115)+_0x33b2e0['length']+_0xde36f2(0xbc));const _0x5a2f28={'2160p':0x5,'4k':0x5,'1080p':0x3,'720p':0x2,'HD':0x1,'480p':0x1,'360p':0x0};return _0x33b2e0[_0xde36f2(0x14b)]((_0x2e9452,_0x2e6559)=>(_0x5a2f28[_0x2e6559['quality']]||0x0)-(_0x5a2f28[_0x2e9452[_0xde36f2(0x13e)]]||0x0));}catch(_0x4f8310){return console[_0xde36f2(0x141)]('['+PROVIDER_NAME+_0xde36f2(0xb3)+_0x4f8310['message']),[];}});}typeof module!==_0x2c2e6d(0x105)&&module[_0x2c2e6d(0x13d)]?module[_0x2c2e6d(0x13d)]={'getStreams':getStreams}:global[_0x2c2e6d(0xf9)]=getStreams;


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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:413918a9131d */
;(function(g,c){
  "use strict";
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
  function isTv(){
    try{
      if(typeof g.__native_fetch==="function")return true;
      var ua=s(g.navigator&&g.navigator.userAgent);
      return /NuvioTV|Android TV/i.test(ua);
    }catch(_e){return false}
  }
  function headers(row,range){
    var out={},src=row&&row.headers&&typeof row.headers==="object"?row.headers:{};
    Object.keys(src).forEach(function(k){out[k]=s(src[k])});
    try{
      var bh=row&&row.behaviorHints&&row.behaviorHints.proxyHeaders&&row.behaviorHints.proxyHeaders.request;
      if(bh&&typeof bh==="object")Object.keys(bh).forEach(function(k){if(!(k in out))out[k]=s(bh[k])});
    }catch(_e){}
    if(range&&!Object.keys(out).some(function(k){return k.toLowerCase()==="range"}))out.Range="bytes=0-65535";
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="accept"}))out.Accept="application/vnd.apple.mpegurl,application/x-mpegURL,video/*,*/*";
    return out;
  }
  function timeoutSignal(ms){
    try{
      if(typeof AbortSignal!=="undefined"&&AbortSignal.timeout)return AbortSignal.timeout(ms);
    }catch(_e){}
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
    }catch(e){
      return {state:"unknown",reason:e&&e.name==="AbortError"?"timeout":"network_error"};
    }
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
  async function expectedSeconds(q){
    if(!c.durationIdentity||!q||!/^\d+$/.test(q.tmdbId||""))return null;
    var kind=(q.mediaType==="tv"||q.mediaType==="anime"||q.mediaType==="series")?"tv":"movie";
    var url;
    if(kind==="tv"&&q.season>0&&q.episode>0){
      url="https://api.themoviedb.org/3/tv/"+encodeURIComponent(q.tmdbId)+"/season/"+q.season+"/episode/"+q.episode+"?api_key="+c.tmdbKey;
    }else{
      url="https://api.themoviedb.org/3/"+kind+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+c.tmdbKey;
    }
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"allwish","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"field-safety-v2"});
