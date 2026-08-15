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
})(typeof globalThis!=="undefined"?globalThis:this,[["YW5pd2F0Y2h0di53YXRjaA==","ww2.aniwatch.fit"]]);
const _0x4c27ee=_0x50b4;(function(_0x2b6eaa,_0x2471d9){const _0x4d23e9=_0x50b4,_0x16a792=_0x2b6eaa();while(!![]){try{const _0xb64360=-parseInt(_0x4d23e9(0x17f))/0x1*(-parseInt(_0x4d23e9(0x1ba))/0x2)+parseInt(_0x4d23e9(0x1a3))/0x3*(parseInt(_0x4d23e9(0x187))/0x4)+-parseInt(_0x4d23e9(0x15d))/0x5*(parseInt(_0x4d23e9(0x1b6))/0x6)+parseInt(_0x4d23e9(0x143))/0x7*(parseInt(_0x4d23e9(0x17e))/0x8)+-parseInt(_0x4d23e9(0x191))/0x9+-parseInt(_0x4d23e9(0x19c))/0xa*(-parseInt(_0x4d23e9(0x17a))/0xb)+-parseInt(_0x4d23e9(0x163))/0xc*(parseInt(_0x4d23e9(0x1b4))/0xd);if(_0xb64360===_0x2471d9)break;else _0x16a792['push'](_0x16a792['shift']());}catch(_0xb8b72c){_0x16a792['push'](_0x16a792['shift']());}}}(_0x210b,0xdc996));var __async=(_0x4d6e64,_0x1479a4,_0x43d1ab)=>{return new Promise((_0x4f420e,_0x28dd29)=>{const _0x4c6612=_0x50b4;var _0x109112=_0x17a146=>{const _0x265b34=_0x50b4;try{_0x19023b(_0x43d1ab[_0x265b34(0x19d)](_0x17a146));}catch(_0x398f04){_0x28dd29(_0x398f04);}},_0x5acb95=_0x5d9149=>{const _0x569b1a=_0x50b4;try{_0x19023b(_0x43d1ab[_0x569b1a(0x183)](_0x5d9149));}catch(_0xf1b57b){_0x28dd29(_0xf1b57b);}},_0x19023b=_0x5c2acd=>_0x5c2acd[_0x4c6612(0x177)]?_0x4f420e(_0x5c2acd['value']):Promise[_0x4c6612(0x1ad)](_0x5c2acd[_0x4c6612(0x185)])[_0x4c6612(0x1b2)](_0x109112,_0x5acb95);_0x19023b((_0x43d1ab=_0x43d1ab[_0x4c6612(0x19e)](_0x4d6e64,_0x1479a4))[_0x4c6612(0x19d)]());});},CryptoJS=require(_0x4c27ee(0x18d)),AGENT=_0x4c27ee(0x196),ALLANIME_BASE=_0x4c27ee(0x158),ALLANIME_API=_0x4c27ee(0x18f);function getSimilarity(_0x25c78b,_0x56bb90){const _0x5bace0=_0x4c27ee;if(!_0x25c78b||!_0x56bb90)return 0x0;const _0x3f2a3f=_0x25c78b[_0x5bace0(0x1b0)]()[_0x5bace0(0x176)](/[^a-z0-9]/g,''),_0x5800a5=_0x56bb90[_0x5bace0(0x1b0)]()[_0x5bace0(0x176)](/[^a-z0-9]/g,'');if(_0x3f2a3f===_0x5800a5)return 0x1;if(_0x3f2a3f[_0x5bace0(0x1c2)]<0x2||_0x5800a5[_0x5bace0(0x1c2)]<0x2)return 0x0;const _0x49297b=_0x512424=>{const _0x2a93ba=_0x5bace0,_0x15de49=new Set();for(let _0x4ec5da=0x0;_0x4ec5da<_0x512424[_0x2a93ba(0x1c2)]-0x1;_0x4ec5da++){_0x15de49[_0x2a93ba(0x16a)](_0x512424[_0x2a93ba(0x179)](_0x4ec5da,_0x4ec5da+0x2));}return _0x15de49;},_0x58bbf6=_0x49297b(_0x3f2a3f),_0x193fef=_0x49297b(_0x5800a5);let _0x339919=0x0;for(const _0x3fa688 of _0x58bbf6){if(_0x193fef[_0x5bace0(0x1b9)](_0x3fa688))_0x339919++;}return 0x2*_0x339919/(_0x58bbf6[_0x5bace0(0x198)]+_0x193fef[_0x5bace0(0x198)]);}function decryptProviderId(_0x586506){const _0x15373e=_0x4c27ee,_0x292af9={'79':'A','7a':'B','7b':'C','7c':'D','7d':'E','7e':'F','7f':'G','70':'H','71':'I','72':'J','73':'K','74':'L','75':'M','76':'N','77':'O','68':'P','69':'Q','6a':'R','6b':'S','6c':'T','6d':'U','6e':'V','6f':'W','60':'X','61':'Y','62':'Z','59':'a','5a':'b','5b':'c','5c':'d','5d':'e','5e':'f','5f':'g','50':'h','51':'i','52':'j','53':'k','54':'l','55':'m','56':'n','57':'o','48':'p','49':'q','4a':'r','4b':'s','4c':'t','4d':'u','4e':'v','4f':'w','40':'x','41':'y','42':'z','08':'0','09':'1','0a':'2','0b':'3','0c':'4','0d':'5','0e':'6','0f':'7','00':'8','01':'9','15':'-','16':'.','67':'_','46':'~','02':':','17':'/','07':'?','1b':'#','63':'[','65':']','78':'@','19':'!','1c':'$','1e':'&','10':'(','11':')','12':'*','13':'+','14':',','03':';','05':'=','1d':'%'};let _0x5b9252='';for(let _0x3c69b7=0x0;_0x3c69b7<_0x586506[_0x15373e(0x1c2)];_0x3c69b7+=0x2){const _0x2cfa35=_0x586506['substring'](_0x3c69b7,_0x3c69b7+0x2);_0x5b9252+=_0x292af9[_0x2cfa35]||_0x2cfa35;}return _0x5b9252[_0x15373e(0x176)](/([^:])\/\//g,_0x15373e(0x1a0))[_0x15373e(0x176)]('/clock',_0x15373e(0x19a));}var AES_KEY=CryptoJS[_0x4c27ee(0x16e)](_0x4c27ee(0x1ab));function decryptToBeParsed(_0x313a64){const _0x200e3e=_0x4c27ee,_0x224a88=CryptoJS[_0x200e3e(0x15a)][_0x200e3e(0x1c1)][_0x200e3e(0x14e)](_0x313a64),_0x57156c=_0x224a88['toString'](CryptoJS[_0x200e3e(0x15a)]['Hex']),_0x5f5dd6=_0x57156c[_0x200e3e(0x179)](0x2,0x2+0x18),_0x213493=_0x57156c[_0x200e3e(0x179)](0x2+0x18,_0x57156c[_0x200e3e(0x1c2)]-0x20);if(!_0x213493||_0x213493['length']===0x0)return null;const _0x4f61c0=_0x5f5dd6+'00000002',_0x1986fc=CryptoJS[_0x200e3e(0x15a)][_0x200e3e(0x154)][_0x200e3e(0x14e)](_0x4f61c0),_0x482034=CryptoJS[_0x200e3e(0x15a)][_0x200e3e(0x154)][_0x200e3e(0x14e)](_0x213493),_0x2a1f73=CryptoJS['lib'][_0x200e3e(0x184)]['create']({'ciphertext':_0x482034}),_0x2b961c=CryptoJS[_0x200e3e(0x18a)][_0x200e3e(0x147)](_0x2a1f73,AES_KEY,{'iv':_0x1986fc,'mode':CryptoJS[_0x200e3e(0x1be)][_0x200e3e(0x1a9)],'padding':CryptoJS[_0x200e3e(0x1bc)][_0x200e3e(0x169)]});return _0x2b961c[_0x200e3e(0x1a8)](CryptoJS[_0x200e3e(0x15a)][_0x200e3e(0x153)]);}function _0x210b(){const _0x296a20=['AxnbCNjHEq','CMvWBgfJzq','zg9Uzq','p3zHCMLHyMXLCZ0','C3vIC3rYAw5N','mZyZvwHmyKLM','CM9TywPP','zdqWnwqWzwrKnJKWnJi0yJy2yMfIytmWnJHLmgvKyZnHyZKWzJe1otDKodK4ytfLyZHKyJrLnwm0m2mWmgzLyW','xsbhB3qG','nZeWodbwvuzRA2e','neDPuuzPqW','ANnVBG','Ahr0Chm6lY8','zMfZDdrZCgvLza','DgHYB3C','q2LWAgvYugfYyw1Z','DMfSDwu','DhLWzq','ngL2veroAq','lcbeDwiGCMvZDwX0CZOG','BwfW','quvt','mta4mha','Dg9IzxbHCNnLzcbku09oihbHCNnLigvYCM9YoG','y3j5ChrVlwPZ','rMv0y2GGChjVDMLKzxiGBgLUA3mGzxjYB3i6','Ahr0Chm6lY9HCgKUywXSyw5PBwuUzgf5l2fWAq','yw5PBgLZDa','otG0odm0uu1Nsu1x','y2f0y2G','ChjVDMLKzxi','C3vI','rMfPBgvKihrVihbHCNnLigrLy3j5ChrLzcb0B2jLCgfYC2vKoG','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYos4WlJaUmcbtywzHCMKVntm3lJm2','zwrNzxm','C2L6zq','l21Wnc9MAwXLlM1Wna','l2nSB2nRlMPZB24','Dg9IzxbHCNnLza','mJK1mdyWAMjNDKXv','BMv4Da','yxbWBhK','u3vIihjLC3vSDhm6ia','jdeV','ihjHDYbZB3vYy2vZ','DxjS','mtiWnda3n3rUBhnyua','zMLSDgvY','Ahr0Chm6lY95B3v0Ds1JAgfUlMnVBq','qwXSqw5PBwuGuMf3ifn0CMvHBsbfCNjVCJO','uY1TCdq','Dg9tDhjPBMC','q1rs','Bw92Awu','wg90mZzPm2XlmZP2mq','C3rHCNrZv2L0Aa','CMvZB2X2zq','DgL0Bgu','qwXSqw5PBwu','Dg9mB3DLCKnHC2u','CMvZB2X1DgLVBLn0CG','DgHLBG','zxbPC29Kzq','mtaXngjAwNfxBa','zw5NBgLZAa','odu3ntHmrMzqufi','Ahr0Chm6lY9HCM0UAgfNBhvUzc5KzxyVyxbPl3yYl3rOzw1VDMLLzgi/Awq9','Aw5JBhvKzxm','AgfZ','mJiZotu0Dw1ZEe5Y','C3rYAw5NAwz5','CgfK','p2fWAv9RzxK9otrMyZDImMe5ztzHzJe0yJfJnZG0nJvKnJrLowuWzde','Bw9Kzq','qw5PBwu','AgvHzgvYCW','qMfZzty0','BgvUz3rO','ihWG','Ahr0Chm6lY9HBgXTyw5Nys50BW','C291CMnLtMfTzq','nJa5Dwzcyu5Y','Bg9N','qxv0BW','C291CMnLvxjSCW','zgvJCNLWDa','AwzYyw1L','zxHWB3j0CW','qwXSqw5PBwuG','xsbtA2LWCgLUzYbPzNjHBwu6ia','qwXSqw5PBwuGu2vHCMnOievYCM9YoG','C3bSAxq','CgfYC2u','zxjYB3i','rgvMyxvSDa','l2fWAxz0D28V','yMvZDa','vxrMoa','sgv4','ywXS','BgLUAW','kI8Q','Ahr0Chm6lY9HBgXHBMLTzs5KyxK','ue9tva','zw5J','C2HVD3m','CxvHBgL0Eq','mteWuM1MC2PN','xsbgywLSzwqGDg8GzgvJCNLWDca','twfWCgLUzYbfCNjVCJO','wxqTBxa0','Ahr0Ca','yxzHAwXHyMXLrxbPC29Kzxm','mtK1mtu2BKvqzKzW','ChvZAa','zhvI','cIaGicaGicaGCxvLCNKGkcrPzdOGsw50ksb7cIaGicaGicaGicaGie1LzgLHicHPzdOGjgLKksb7cIaGicaGicaGicaGicaGicbPzaOGicaGicaGicaGicaGicaGzM9YBwf0cIaGicaGicaGicaGicaGicbLCgLZB2rLCWOGicaGicaGicaGicaGicaGDgL0BguGEYbYB21HAMKGzw5NBgLZAcbUyxrPDMuGFqOGicaGicaGicaGicaGicaGCMvSyxrPB25ZihSkicaGicaGicaGicaGicaGicaGicbLzgDLCYb7ihjLBgf0Aw9UvhLWzsb9cIaGicaGicaGicaGicaGicaGicaGBM9KzxmGEYbPzcbMB3jTyxqGzxbPC29KzxmGDhLWzsb9cIaGicaGicaGicaGicaGicb9cIaGicaGicaGicaGih0kicaGicaGicb9cIaGica','yxbWBgLJyxrPB24VANnVBG','thvMlu1Wna','tM9qywrKAw5N','ywrK','u2vHCMnOihrPDgXLoG','z2v0uMf3u3rYzwfTu291CMnLCYbivfrq','BMfTzq','u0HbmJu2','zgf0yq','Bwf0y2G','uMvZB2X2zwq6','vxyTBxa0','BgLUA3m','vw5RBM93BG'];_0x210b=function(){return _0x296a20;};return _0x210b();}function searchAnime(_0x39b928,_0x117a37){return __async(this,null,function*(){const _0x19d160=_0x50b4;var _0x1080b6,_0x36d801;const _0x274e20=_0x117a37===_0x19d160(0x165)?_0x19d160(0x165):_0x19d160(0x194),_0x336c59='query(\x20$search:\x20SearchInput\x20$limit:\x20Int\x20$page:\x20Int\x20$translationType:\x20VaildTranslationTypeEnumType\x20$countryOrigin:\x20VaildCountryOriginEnumType\x20)\x20{\x20shows(\x20search:\x20$search\x20limit:\x20$limit\x20page:\x20$page\x20translationType:\x20$translationType\x20countryOrigin:\x20$countryOrigin\x20)\x20{\x20edges\x20{\x20_id\x20name\x20availableEpisodes\x20__typename\x20}\x20}}',_0x2ec480=JSON[_0x19d160(0x1bb)]({'variables':{'search':{'allowAdult':![],'allowUnknown':![],'query':_0x39b928},'limit':0x28,'page':0x1,'translationType':_0x274e20,'countryOrigin':'ALL'},'query':_0x336c59}),_0x212bc1={'User-Agent':AGENT,'Content-Type':_0x19d160(0x167),'Referer':_0x19d160(0x1c4),'Origin':_0x19d160(0x1c4)};try{const _0x2a23db=yield fetch(ALLANIME_API,{'method':_0x19d160(0x159),'headers':_0x212bc1,'body':_0x2ec480});if(!_0x2a23db['ok'])return[];const _0x4a4ac1=yield _0x2a23db[_0x19d160(0x180)](),_0x5a0c53=((_0x36d801=(_0x1080b6=_0x4a4ac1==null?void 0x0:_0x4a4ac1[_0x19d160(0x16f)])==null?void 0x0:_0x1080b6[_0x19d160(0x15b)])==null?void 0x0:_0x36d801[_0x19d160(0x197)])||[];return _0x5a0c53[_0x19d160(0x189)](_0x51c079=>({'id':_0x51c079['_id'],'name':_0x51c079[_0x19d160(0x16d)],'episodes':_0x51c079[_0x19d160(0x162)]&&_0x51c079[_0x19d160(0x162)][_0x274e20]||0x0}));}catch(_0x24a9b5){return console['error'](_0x19d160(0x14c),_0x24a9b5),[];}});}function getRawStreamSources(_0x4feff4,_0x3055fe,_0x4228cd){return __async(this,null,function*(){const _0x563f32=_0x50b4;var _0x41d349,_0x232cef,_0x2de22d,_0x538cff;const _0x3e122a=_0x4228cd==='dub'?_0x563f32(0x165):'sub',_0x5ddac9={'showId':_0x4feff4,'translationType':_0x3e122a,'episodeString':String(_0x3055fe)},_0x3d4933=_0x563f32(0x17c),_0x5ebad0=ALLANIME_API+_0x563f32(0x178)+encodeURIComponent(JSON['stringify'](_0x5ddac9))+'&extensions='+encodeURIComponent(JSON[_0x563f32(0x1bb)]({'persistedQuery':{'version':0x1,'sha256Hash':_0x3d4933}})),_0x530f6c={'User-Agent':AGENT,'Accept':_0x563f32(0x157),'Referer':_0x563f32(0x1a5),'Origin':ALLANIME_BASE};try{const _0xf1d365=yield fetch(_0x5ebad0,{'headers':_0x530f6c});if(!_0xf1d365['ok'])return console[_0x563f32(0x14f)](_0x563f32(0x16c),_0xf1d365['status']),[];const _0x8ec7a0=yield _0xf1d365[_0x563f32(0x180)]();if((_0x41d349=_0x8ec7a0==null?void 0x0:_0x8ec7a0['data'])==null?void 0x0:_0x41d349[_0x563f32(0x19b)]){const _0x298734=decryptToBeParsed(_0x8ec7a0[_0x563f32(0x16f)]['tobeparsed']);if(_0x298734)try{const _0x1bb6c9=JSON[_0x563f32(0x14e)](_0x298734);if((_0x232cef=_0x1bb6c9==null?void 0x0:_0x1bb6c9[_0x563f32(0x1b3)])==null?void 0x0:_0x232cef[_0x563f32(0x146)])return _0x1bb6c9[_0x563f32(0x1b3)]['sourceUrls'];}catch(_0x5af37b){console[_0x563f32(0x14f)](_0x563f32(0x18c),_0x5af37b,_0x298734['substring'](0x0,0x64));}return[];}return((_0x538cff=(_0x2de22d=_0x8ec7a0==null?void 0x0:_0x8ec7a0['data'])==null?void 0x0:_0x2de22d[_0x563f32(0x1b3)])==null?void 0x0:_0x538cff[_0x563f32(0x146)])||[];}catch(_0x4e560d){return console['error'](_0x563f32(0x1a6),_0x4e560d),[];}});}function fetchLinksFromProvider(_0x3e9921){return __async(this,null,function*(){const _0x4265f0=_0x50b4;try{const _0x2fd86d=_0x3e9921['startsWith'](_0x4265f0(0x161))?_0x3e9921:ALLANIME_BASE+_0x3e9921,_0x5115b2=yield fetch(_0x2fd86d,{'headers':{'User-Agent':AGENT,'Referer':ALLANIME_BASE+'/'}});if(!_0x5115b2['ok'])return[];const _0x17e8e1=yield _0x5115b2[_0x4265f0(0x180)](),_0x117979=[];if(_0x17e8e1['links']&&Array[_0x4265f0(0x175)](_0x17e8e1[_0x4265f0(0x173)]))_0x117979[_0x4265f0(0x164)](..._0x17e8e1['links'][_0x4265f0(0x189)](_0xb2b7a9=>({'url':_0xb2b7a9[_0x4265f0(0x156)],'quality':_0xb2b7a9[_0x4265f0(0x1b1)]||'Unknown','headers':{'User-Agent':AGENT}})));else{if(_0x17e8e1[_0x4265f0(0x16f)]){const _0x50f325=decryptToBeParsed(_0x17e8e1['data']);try{const _0x5f2b11=JSON[_0x4265f0(0x14e)](_0x50f325),_0x50eb83=Array['isArray'](_0x5f2b11)?_0x5f2b11:_0x5f2b11['links']||[];_0x117979[_0x4265f0(0x164)](..._0x50eb83[_0x4265f0(0x189)](_0xd985b4=>({'url':_0xd985b4['link'],'quality':_0xd985b4['resolutionStr']||'Unknown','headers':{'User-Agent':AGENT}})));}catch(_0x45ebe5){console[_0x4265f0(0x14f)](_0x4265f0(0x195),_0x45ebe5);}}}return _0x117979;}catch(_0x58e08e){return console[_0x4265f0(0x14f)](_0x4265f0(0x18e),_0x58e08e),[];}});}function _0x50b4(_0x5cb40f,_0x2b5308){_0x5cb40f=_0x5cb40f-0x143;const _0x210b00=_0x210b();let _0x50b444=_0x210b00[_0x5cb40f];if(_0x50b4['sGfBNi']===undefined){var _0x6bd1cf=function(_0x1c3d89){const _0x4e39a1='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x4d6e64='',_0x1479a4='';for(let _0x43d1ab=0x0,_0x4f420e,_0x28dd29,_0x109112=0x0;_0x28dd29=_0x1c3d89['charAt'](_0x109112++);~_0x28dd29&&(_0x4f420e=_0x43d1ab%0x4?_0x4f420e*0x40+_0x28dd29:_0x28dd29,_0x43d1ab++%0x4)?_0x4d6e64+=String['fromCharCode'](0xff&_0x4f420e>>(-0x2*_0x43d1ab&0x6)):0x0){_0x28dd29=_0x4e39a1['indexOf'](_0x28dd29);}for(let _0x5acb95=0x0,_0x19023b=_0x4d6e64['length'];_0x5acb95<_0x19023b;_0x5acb95++){_0x1479a4+='%'+('00'+_0x4d6e64['charCodeAt'](_0x5acb95)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x1479a4);};_0x50b4['qViKss']=_0x6bd1cf,_0x50b4['MggyNI']={},_0x50b4['sGfBNi']=!![];}const _0x1336d4=_0x210b00[0x0],_0x3ebf01=_0x5cb40f+_0x1336d4,_0x1092d5=_0x50b4['MggyNI'][_0x3ebf01];return!_0x1092d5?(_0x50b444=_0x50b4['qViKss'](_0x50b444),_0x50b4['MggyNI'][_0x3ebf01]=_0x50b444):_0x50b444=_0x1092d5,_0x50b444;}function getAnilistId(_0xca0663,_0x2351c1){return __async(this,null,function*(){const _0x7d7c5a=_0x50b4;try{const _0x41a075=_0x7d7c5a(0x1b7)+_0xca0663,_0x46f521=yield fetch(_0x41a075);if(_0x46f521['ok']){const _0x108b74=yield _0x46f521[_0x7d7c5a(0x180)]();if(Array['isArray'](_0x108b74)&&_0x108b74['length']>0x0&&_0x108b74[0x0][_0x7d7c5a(0x190)])return _0x108b74[0x0][_0x7d7c5a(0x190)];}}catch(_0x4bd60e){console['error'](_0x7d7c5a(0x15f),_0x4bd60e);}return null;});}function getAnilistMeta(_0x4a3456){return __async(this,null,function*(){const _0x235ae9=_0x50b4;var _0x2e8be1;const _0x1d0027=_0x235ae9(0x166);try{const _0xb3e40c=yield fetch('https://graphql.anilist.co',{'method':'POST','headers':{'Content-Type':_0x235ae9(0x167),'Accept':'application/json'},'body':JSON[_0x235ae9(0x1bb)]({'query':_0x1d0027,'variables':{'id':parseInt(_0x4a3456)}})});if(_0xb3e40c['ok']){const _0x3fc055=yield _0xb3e40c[_0x235ae9(0x180)]();return(_0x2e8be1=_0x3fc055[_0x235ae9(0x16f)])==null?void 0x0:_0x2e8be1['Media'];}}catch(_0x32d788){}return null;});}function resolveAnilistEpisode(_0x5b8b85,_0x4f282e,_0x3409d1,_0xfab697){return __async(this,null,function*(){const _0x341e6e=_0x50b4,_0x75f294=yield getAnilistMeta(_0x5b8b85);if(!_0x75f294)return{'title':null,'ep':_0x3409d1};const _0x3ac1d2=_0x75f294[_0x341e6e(0x1ae)][_0x341e6e(0x17b)]||_0x75f294['title'][_0x341e6e(0x1b5)]||'';return{'title':_0x3ac1d2,'ep':_0x3409d1};});}function getStreams(_0x4fdcbd,_0x201f36,_0x1e9786,_0x4e7317){return __async(this,null,function*(){const _0x147f6e=_0x50b4,_0x29e328=_0x4fdcbd,_0x585b61=yield getAnilistId(_0x29e328,_0x201f36);console[_0x147f6e(0x144)]('Anilist\x20ID:',_0x585b61);let _0x242caa=_0x147f6e(0x1bf),_0x414797=String(_0x4e7317),_0x641ea2=String(_0x4e7317);if(_0x585b61){const _0x51ec9a=yield resolveAnilistEpisode(_0x585b61,_0x1e9786,_0x4e7317,_0x201f36);console[_0x147f6e(0x144)](_0x147f6e(0x171),_0x51ec9a),_0x242caa=_0x51ec9a[_0x147f6e(0x1ae)]||_0x242caa,_0x414797=String(_0x51ec9a['ep']),_0x641ea2=String(_0x51ec9a['ep']);}else try{const _0x454ae8=yield fetch('https://api.themoviedb.org/3/'+(_0x201f36===_0x147f6e(0x1aa)?_0x147f6e(0x1aa):'tv')+'/'+_0x29e328+_0x147f6e(0x1bd));if(_0x454ae8['ok']){const _0x57f89b=yield _0x454ae8[_0x147f6e(0x180)]();_0x242caa=_0x57f89b[_0x147f6e(0x16d)]||_0x57f89b[_0x147f6e(0x1ae)]||_0x242caa;}}catch(_0x3cfcaa){}console[_0x147f6e(0x144)](_0x147f6e(0x16b),_0x242caa);const _0xa0ca3e=[_0x242caa],[_0x42ee0b,_0x30443b]=yield Promise[_0x147f6e(0x155)]([searchAnime(_0xa0ca3e[0x0],_0x147f6e(0x194))[_0x147f6e(0x192)](()=>[]),searchAnime(_0xa0ca3e[0x0],'dub')[_0x147f6e(0x192)](()=>[])]);console[_0x147f6e(0x144)](_0x147f6e(0x19f)+_0x42ee0b[_0x147f6e(0x1c2)]+_0x147f6e(0x188)+_0x30443b[_0x147f6e(0x1c2)]);const _0x35cac6=(_0x364788,_0x4a1f3a)=>{const _0x245c94=_0x147f6e;if(!_0x364788||_0x364788[_0x245c94(0x1c2)]===0x0)return null;let _0x10f9dc=0x0,_0x47676f=null;for(const _0x1551fe of _0x364788){const _0x3ddd05=getSimilarity(_0x1551fe[_0x245c94(0x16d)],_0x4a1f3a);_0x3ddd05>_0x10f9dc&&(_0x10f9dc=_0x3ddd05,_0x47676f=_0x1551fe);}if(_0x47676f&&_0x10f9dc>0.4)return _0x47676f;return _0x364788[0x0];};let _0x30f471=_0x35cac6(_0x42ee0b,_0x242caa),_0x5a10bc=_0x35cac6(_0x30443b,_0x242caa);const _0x328a1a=[],_0x3ece6d=(_0x23982e,_0x25454c,_0x57f403)=>__async(this,null,function*(){const _0x139973=_0x147f6e;if(!_0x23982e)return;const _0x4d65af=yield getRawStreamSources(_0x23982e['id'],_0x57f403,_0x25454c[_0x139973(0x1b0)]());console[_0x139973(0x144)]('['+_0x25454c+_0x139973(0x17d)+_0x4d65af['length']+_0x139973(0x1a1));const _0x2b948d=[_0x139973(0x160),_0x139973(0x150),_0x139973(0x1a7),_0x139973(0x172),_0x139973(0x168),'Sl-mp4'];for(const _0x55c20b of _0x4d65af){const _0x1e51c1=_0x55c20b[_0x139973(0x1c5)]||'';let _0x3d56cf=_0x55c20b['sourceUrl'];if(_0x3d56cf['startsWith']('--')){_0x3d56cf=decryptProviderId(_0x3d56cf['substring'](0x2));if(!_0x3d56cf){console[_0x139973(0x144)]('['+_0x25454c+_0x139973(0x15e)+_0x1e51c1);continue;}}console[_0x139973(0x144)]('['+_0x25454c+']\x20'+_0x1e51c1+':\x20'+_0x3d56cf[_0x139973(0x179)](0x0,0x50));if(_0x3d56cf[_0x139973(0x1b8)](_0x139973(0x182))){_0x328a1a[_0x139973(0x164)]({'url':_0x3d56cf,'quality':'1080p','provider':_0x139973(0x14a)+_0x1e51c1+'\x20('+_0x25454c+')','headers':{'Referer':_0x139973(0x158),'User-Agent':AGENT}});continue;}if(_0x3d56cf[_0x139973(0x1b8)](_0x139973(0x19a))||_0x3d56cf['includes'](_0x139973(0x151))){const _0x19e4a1=_0x3d56cf[_0x139973(0x1ac)](_0x139973(0x161))?_0x3d56cf:ALLANIME_BASE+_0x3d56cf,_0x21fea8=yield fetchLinksFromProvider(_0x19e4a1);for(const _0x347fa5 of _0x21fea8){const _0x312468=_0x347fa5[_0x139973(0x1a2)]||'';if(!_0x312468)continue;const _0x3d5aca=_0x312468[_0x139973(0x170)](/repackager\.wixmp\.com\/([^,]+)\/((?:,[^,]+)+,?)\/mp4\/file\.mp4/);if(_0x3d5aca){const _0x5b17ff=_0x3d5aca[0x1],_0x496b2f=_0x3d5aca[0x2][_0x139973(0x14d)](',')[_0x139973(0x1a4)](_0x4429ca=>_0x4429ca[_0x139973(0x1c2)]>0x0);for(const _0x473afe of _0x496b2f){_0x328a1a[_0x139973(0x164)]({'url':_0x139973(0x181)+_0x5b17ff+'/'+_0x473afe+_0x139973(0x199),'quality':_0x473afe,'provider':_0x139973(0x14a)+_0x1e51c1+'\x20('+_0x25454c+')','headers':{'User-Agent':AGENT}});}}else _0x328a1a[_0x139973(0x164)]({'url':_0x312468,'quality':_0x347fa5[_0x139973(0x15c)]||_0x347fa5[_0x139973(0x1b1)]||_0x139973(0x145),'provider':_0x139973(0x14a)+_0x1e51c1+'\x20('+_0x25454c+')','headers':Object['assign']({'Referer':'https://allanime.day'},_0x347fa5[_0x139973(0x1c0)]||{})});}continue;}if(_0x55c20b[_0x139973(0x186)]===_0x139973(0x148)){console[_0x139973(0x144)]('['+_0x25454c+_0x139973(0x14b)+_0x1e51c1);continue;}}});return yield Promise[_0x147f6e(0x155)]([_0x3ece6d(_0x30f471,'Sub',_0x414797),_0x3ece6d(_0x5a10bc,'Dub',_0x641ea2)]),_0x328a1a[_0x147f6e(0x189)](_0x41e1e5=>{const _0x4d4b6a=_0x147f6e;let _0xd3b67b=_0x4d4b6a(0x174);if(_0x41e1e5[_0x4d4b6a(0x15c)]){const _0xb148ad=_0x41e1e5['quality'][_0x4d4b6a(0x170)](/\d+p/i);if(_0xb148ad)_0xd3b67b=_0xb148ad[0x0];else{if(_0x41e1e5['quality']['toLowerCase']()===_0x4d4b6a(0x152))_0xd3b67b=_0x4d4b6a(0x18b);}}return{'name':_0x41e1e5[_0x4d4b6a(0x193)],'title':_0x41e1e5[_0x4d4b6a(0x193)]+_0x4d4b6a(0x1c3)+_0x41e1e5[_0x4d4b6a(0x15c)],'url':_0x41e1e5[_0x4d4b6a(0x1a2)],'quality':_0xd3b67b,'headers':_0x41e1e5[_0x4d4b6a(0x1c0)]};});});}module[_0x4c27ee(0x149)]={'name':_0x4c27ee(0x1af),'getStreams':getStreams};


/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3:a95c2454c09d */
;(function(g,c){"use strict";
var K="8265bd1679663a7ea12ac168da84d2e8";
var J={},C={};
function s(v){return String(v==null?"":v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").trim()}
function n(v){try{return s(v).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}catch(_){return s(v).toLowerCase()}}
function slug(v){return n(v).replace(/\s+/g,"-")}
function abs(v,b){try{return new URL(s(v),b).toString()}catch(_){return ""}}
function origin(v){try{return new URL(v).origin}catch(_){return ""}}
function bad(u){try{var x=new URL(u),h=x.hostname.toLowerCase(),p=x.pathname.toLowerCase();if(!/^https?:$/.test(x.protocol))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;for(var j=0;j<c.blockedPaths.length;j++)if(p.indexOf(c.blockedPaths[j])>=0)return true;return /(?:google-analytics|googletagmanager|cloudflareinsights|telegram\.org\/img|datatracker\.ietf\.org)/i.test(u)||/\.(?:js|css|woff2?|ttf|png|jpe?g|gif|svg)(?:[?#]|$)/i.test(p)}catch(_){return true}}
function mediaType(t){return /(?:application\/(?:vnd\.apple\.mpegurl|x-mpegurl|dash\+xml)|audio\/(?:mpegurl|x-mpegurl)|video\/)/i.test(s(t))}
function media(u,t,b){return !bad(u)&&(/\.(?:m3u8|mp4|mpd|mkv|webm)(?:[?#]|$)/i.test(u)||mediaType(t)||/^\s*#EXTM3U/i.test(s(b)))}
function parseCookies(values){var out={};for(var i=0;i<values.length;i++){var line=s(values[i]),pair=line.split(";",1)[0],p=pair.indexOf("=");if(p>0)out[pair.slice(0,p).trim()]=pair.slice(p+1).trim()}return out}
function saveCookies(u,h){try{var o=origin(u),values=[];if(h&&typeof h.getSetCookie==="function")values=h.getSetCookie()||[];if(!values.length&&h&&typeof h.get==="function"){var one=h.get("set-cookie");if(one)values=[one]}var next=parseCookies(values),cur=J[o]||{};Object.keys(next).forEach(function(k){cur[k]=next[k]});J[o]=cur}catch(_){}}
function cookieHeader(u,ref){var bag=Object.assign({},J[origin(ref)]||{},J[origin(u)]||{}),parts=[];Object.keys(bag).forEach(function(k){parts.push(k+"="+bag[k])});return parts.join("; ")}
function hdr(ref,target){var h={Referer:ref,"Accept-Language":"fr-FR,fr;q=0.9,en;q=0.5"};try{h.Origin=new URL(ref).origin}catch(_){}var ck=cookieHeader(target||ref,ref);if(ck)h.Cookie=ck;return h}
function wait(ms){return new Promise(function(resolve){setTimeout(resolve,ms)})}
async function req(u,json,ref,attempt){attempt=attempt||0;var key=(json?"j":"t")+"|"+u+"|"+s(ref);if(C[key])return C[key];var a=new AbortController(),t=setTimeout(function(){a.abort()},c.timeoutMs),headers=Object.assign({Accept:json?"application/json,text/plain,*/*":"text/html,application/xhtml+xml,application/json,video/*,*/*"},ref?hdr(ref,u):{}),r=null;try{try{r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}catch(e){if(headers.Cookie){delete headers.Cookie;r=await g.fetch(u,{redirect:"follow",headers:headers,signal:a.signal})}else throw e}if(!r)return null;saveCookies(r.url||u,r.headers);if(r.status===429&&attempt<1){clearTimeout(t);await wait(900);return req(u,json,ref,attempt+1)}if(!r.ok)return null;var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",body=null;if(json){body=await r.json()}else if(media(finalUrl,type,"")){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,status:r.status};C[key]=result;return result}catch(_){return null}finally{clearTimeout(t)}}
function args(a){var q=a[0]&&typeof a[0]==="object"?Object.assign({},a[0]):{tmdbId:a[0],mediaType:a[1],season:a[2],episode:a[3],settings:a[4]||{}};q.tmdbId=s(q.tmdbId||q.id);q.mediaType=s(q.mediaType||q.type||"movie").toLowerCase();return q}
async function meta(q){var title=s(q.title||q.name||q.label),year=Number(q.year)||0;if(!title&&q.tmdbId){var k=q.mediaType==="tv"?"tv":"movie",d=await req("https://api.themoviedb.org/3/"+k+"/"+encodeURIComponent(q.tmdbId)+"?api_key="+K+"&language=fr-FR",true);if(d&&d.body){title=s(d.body.title||d.body.name);year=Number(s(d.body.release_date||d.body.first_air_date).slice(0,4))||year}}return {title:title.replace(/\s*\(\d{4}\)\s*$/,"") ,year:year}}
function urls(html,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var t=s(html),res=[/(?:href|src|data-src|data-url|data-embed|data-player|data-video|data-link)=["']([^"']+)["']/gi,/(?:file|source|url|embedUrl|embed_url|contentUrl|content_url|playlist)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s]+(?:m3u8|mp4|mpd|mkv|webm)(?:\?[^"'<>\s]*)?)/gi],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add(m[1]);return out}
function score(u,m,q){var z=n(u),w=n(m.title),v=0;if(w&&z.indexOf(w)>=0)v+=80;w.split(" ").filter(function(x){return x.length>2}).forEach(function(x){if(z.indexOf(x)>=0)v+=8});if(m.year&&z.indexOf(String(m.year))>=0)v+=20;if(q.mediaType==="tv"&&new RegExp("(?:s|saison)[^0-9]*0?"+(Number(q.season)||1)+".*(?:e|ep|episode)[^0-9]*0?"+(Number(q.episode)||1),"i").test(z))v+=60;return v}
function playerScore(u,parent){if(media(u,"",""))return 1000;try{var a=new URL(u),b=new URL(parent),v=0;if(a.origin!==b.origin)v+=80;if(/(?:embed|player|video|watch|stream|playlist|\/e\/|\/v\/)/i.test(a.pathname+a.search))v+=160;if(/(?:dailymotion|lecteurvideo|sharecloudy|sibnet|vidmoly|vidzy|streamtape|sendvid|vidoza|uqload|voe)/i.test(a.hostname))v+=220;return v}catch(_){return -1}}
function unique(rows){var out=[],seen={};for(var i=0;i<rows.length;i++){var row=rows[i],u=s(row&&row.url);if(!u||seen[u])continue;seen[u]=1;out.push(row)}return out}
function normalizedPlayers(body,page){var out=[],seen={};function add(u){u=abs(u,page);if(!u||bad(u)||seen[u])return;seen[u]=1;out.push(u)}var h="";try{h=new URL(page).hostname.toLowerCase()}catch(_){}if(/(?:^|\.)dailymotion\.com$/.test(h)){var t=s(body),res=[/(?:videoId|video_id|video)\s*["']?\s*[:=]\s*["']([a-zA-Z0-9]+)["']/g,/\/video\/([a-zA-Z0-9]+)/g],m;for(var i=0;i<res.length;i++)while((m=res[i].exec(t))!==null)add("https://www.dailymotion.com/embed/video/"+m[1])}return out}
async function resolve(u,ref,depth,seen){if(depth>c.maxDepth||bad(u))return [];seen=seen||{};var requested=u;if(seen[requested])return [];seen[requested]=1;if(media(requested,"",""))return [{url:requested,referer:ref||requested}];var doc=await req(requested,false,ref);if(!doc)return [];var page=doc.url||requested;if(seen[page]&&page!==requested)return [];seen[page]=1;if(media(page,doc.type,doc.body))return [{url:page,referer:ref||requested}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));xs=Array.from(new Set(xs)).sort(function(a,b){return playerScore(b,page)-playerScore(a,page)});var out=[];for(var d=0;d<xs.length;d++)if(media(xs[d],"",""))out.push({url:xs[d],referer:page});for(var i=0;i<xs.length&&i<c.maxEmbeds&&out.length<c.maxEmbeds;i++){if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);if(ps<80)continue;var r=await resolve(xs[i],page,depth+1,seen);out=out.concat(r)}return unique(out).slice(0,c.maxEmbeds)}
async function recover(q){if(c.types.indexOf(q.mediaType)<0)return [];var m=await meta(q);if(!m.title)return [];var cand=[],sl=slug(m.title),sharedSeen={};for(var i=0;i<c.directPaths.length;i++)cand.push(abs(c.directPaths[i].replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId).replace(/\{year\}/g,String(m.year||"")),c.baseUrl+"/"));for(var j=0;j<c.searchPaths.length;j++){var u=abs(c.searchPaths[j].replace(/\{query\}/g,encodeURIComponent(m.title)).replace(/\{slug\}/g,sl).replace(/\{id\}/g,q.tmdbId),c.baseUrl+"/"),doc=await req(u,false,c.baseUrl+"/");if(doc&&doc.body)cand=cand.concat(urls(doc.body,doc.url||u).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages))}cand=Array.from(new Set(cand)).sort(function(a,b){return score(b,m,q)-score(a,m,q)}).slice(0,c.maxPages);var found=[];for(var k=0;k<cand.length&&found.length<c.maxEmbeds;k++){var r=await resolve(cand[k],c.baseUrl+"/",0,sharedSeen);found=found.concat(r)}return unique(found).slice(0,c.maxEmbeds).map(function(row,i){return {name:c.providerName+(i?" #"+(i+1):""),title:c.providerName+" - "+m.title,url:row.url,quality:"HD",headers:hdr(row.referer||c.baseUrl+"/",row.url),isDirect:media(row.url,"","")}})}
function install(o,k){if(!o||typeof o[k]!=="function"||o[k].__nuvioAdaptive)return false;var old=o[k];var w=async function(){var native=[];try{native=await old.apply(this,arguments)}catch(_){}if(Array.isArray(native)&&native.some(function(x){return x&&media(s(x.url),"","")}))return native;var r=await recover(args(arguments));return r.length?r:(Array.isArray(native)?native:[])};w.__nuvioAdaptive=true;o[k]=w;return true}
var ok=false;try{if(typeof module!=="undefined"&&module.exports)ok=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(ok&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerName":"AllAnime","baseUrl":"https://ww2.aniwatch.fit","types":["movie","tv"],"searchPaths":["/?s={query}","/search?q={query}","/index.php?do=search&subaction=search&story={query}"],"directPaths":["/{slug}","/film/{slug}","/films/{slug}","/anime/{slug}","/serie/{slug}","/series/{slug}"],"maxPages":10,"maxEmbeds":10,"maxDepth":3,"timeoutMs":9000,"blockedHosts":["cloudflareinsights.com","connect.facebook.net","doubleclick.net","fstream.top","google-analytics.com","googlesyndication.com","googletagmanager.com","static.cloudflareinsights.com"],"blockedPaths":["/beacon.min.js","/cdn-cgi/rum","/gtag/js","/troll/"]});

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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:2fbdb910e141 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"allanime","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
