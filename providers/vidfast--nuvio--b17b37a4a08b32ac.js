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
})(typeof globalThis!=="undefined"?globalThis:this,[["dmlkZmFzdC5wcm8=","vidfast.vc"]]);
const _0x2f4cb9=_0x42d0;(function(_0xd71400,_0x4ebb4c){const _0x1c797e={_0x306088:0x134,_0x2e05ee:0x12d,_0xed414b:0x121,_0x3d0edc:0x11e,_0x75aedf:0x140},_0x46f2f5=_0x42d0,_0x4990bf=_0xd71400();while(!![]){try{const _0x3c5c7d=parseInt(_0x46f2f5(0x116))/0x1*(-parseInt(_0x46f2f5(0x142))/0x2)+-parseInt(_0x46f2f5(_0x1c797e._0x306088))/0x3*(-parseInt(_0x46f2f5(0x13c))/0x4)+-parseInt(_0x46f2f5(_0x1c797e._0x2e05ee))/0x5*(parseInt(_0x46f2f5(0x122))/0x6)+-parseInt(_0x46f2f5(0xfe))/0x7+-parseInt(_0x46f2f5(_0x1c797e._0xed414b))/0x8*(parseInt(_0x46f2f5(0x10b))/0x9)+parseInt(_0x46f2f5(_0x1c797e._0x3d0edc))/0xa+parseInt(_0x46f2f5(_0x1c797e._0x75aedf))/0xb;if(_0x3c5c7d===_0x4ebb4c)break;else _0x4990bf['push'](_0x4990bf['shift']());}catch(_0x37fdc9){_0x4990bf['push'](_0x4990bf['shift']());}}}(_0x55f9,0x2bca0));var __defProp=Object[_0x2f4cb9(0x100)],__defProps=Object[_0x2f4cb9(0x136)],__getOwnPropDescs=Object[_0x2f4cb9(0x106)],__getOwnPropSymbols=Object[_0x2f4cb9(0x104)],__hasOwnProp=Object['prototype'][_0x2f4cb9(0x127)],__propIsEnum=Object[_0x2f4cb9(0x132)]['propertyIsEnumerable'],__defNormalProp=(_0x77a907,_0x2bdc2d,_0x5dd5e3)=>_0x2bdc2d in _0x77a907?__defProp(_0x77a907,_0x2bdc2d,{'enumerable':!![],'configurable':!![],'writable':!![],'value':_0x5dd5e3}):_0x77a907[_0x2bdc2d]=_0x5dd5e3,__spreadValues=(_0x27347d,_0x3f6085)=>{const _0x17aaaf={_0x4246bc:0xfa},_0x1d0132=_0x2f4cb9;for(var _0x5dc583 in _0x3f6085||(_0x3f6085={}))if(__hasOwnProp[_0x1d0132(_0x17aaaf._0x4246bc)](_0x3f6085,_0x5dc583))__defNormalProp(_0x27347d,_0x5dc583,_0x3f6085[_0x5dc583]);if(__getOwnPropSymbols)for(var _0x5dc583 of __getOwnPropSymbols(_0x3f6085)){if(__propIsEnum[_0x1d0132(0xfa)](_0x3f6085,_0x5dc583))__defNormalProp(_0x27347d,_0x5dc583,_0x3f6085[_0x5dc583]);}return _0x27347d;},__spreadProps=(_0x3f444a,_0x4e8f50)=>__defProps(_0x3f444a,__getOwnPropDescs(_0x4e8f50)),__async=(_0x1d9281,_0x3ddae7,_0x393a24)=>{const _0x49342e={_0x53cc1c:0x130};return new Promise((_0x1bb2b2,_0xd7a452)=>{const _0x134bbe=_0x42d0;var _0x4d6dd6=_0x3ee842=>{try{_0x288ab2(_0x393a24['next'](_0x3ee842));}catch(_0x4d727e){_0xd7a452(_0x4d727e);}},_0x48bb8c=_0x1fc61e=>{try{_0x288ab2(_0x393a24['throw'](_0x1fc61e));}catch(_0x4e61b0){_0xd7a452(_0x4e61b0);}},_0x288ab2=_0x295b73=>_0x295b73[_0x134bbe(0x120)]?_0x1bb2b2(_0x295b73[_0x134bbe(0xff)]):Promise['resolve'](_0x295b73['value'])['then'](_0x4d6dd6,_0x48bb8c);_0x288ab2((_0x393a24=_0x393a24['apply'](_0x1d9281,_0x3ddae7))[_0x134bbe(_0x49342e._0x53cc1c)]());});},VIDFAST_API=_0x2f4cb9(0xf6),DECRYPT_API=_0x2f4cb9(0x137),HEADERS={'User-Agent':_0x2f4cb9(0x123),'Referer':'https://vidfast.vc/','X-Requested-With':_0x2f4cb9(0x126)};function generateM3u8(_0x4f3e7f){const _0x51424a={_0x114aac:0x131,_0x34737d:0x112,_0x247f07:0x101,_0x69a086:0xf7,_0x1cdd11:0x10e,_0x3d5057:0x105};return __async(this,arguments,function*(_0x616417,_0x35cabd={}){const _0x45961d=_0x42d0;try{console['log'](_0x45961d(0x13a)+_0x616417);const _0x2ff104=yield fetch(_0x616417,{'headers':_0x35cabd}),_0x5bfcd9=yield _0x2ff104[_0x45961d(0xf8)](),_0x5864cc=_0x616417[_0x45961d(0x10d)](0x0,_0x616417[_0x45961d(_0x51424a._0x114aac)]('/'))+'/',_0x197bd0=[],_0x11fdb1=/#EXT-X-STREAM-INF:.*?RESOLUTION=(\d+x\d+).*?\n([^\n]+)/g;let _0x215013;while((_0x215013=_0x11fdb1[_0x45961d(_0x51424a._0x34737d)](_0x5bfcd9))!==null){const _0x256ad2=parseInt(_0x215013[0x1][_0x45961d(0x119)]('x')[0x1]);if(_0x256ad2<0x2d0)continue;const _0x39ba86=_0x256ad2+'p';let _0x31a7ef=_0x215013[0x2][_0x45961d(_0x51424a._0x247f07)]();if(!_0x31a7ef['startsWith'](_0x45961d(0x125))){if(_0x31a7ef[_0x45961d(0x115)]('/')){const _0x469059=new URL(_0x616417)['origin'];_0x31a7ef=_0x469059+_0x31a7ef;}else _0x31a7ef=_0x5864cc+_0x31a7ef;}_0x197bd0[_0x45961d(_0x51424a._0x69a086)]({'quality':_0x39ba86,'url':_0x31a7ef});}return _0x197bd0;}catch(_0x3ee653){return console[_0x45961d(_0x51424a._0x1cdd11)](_0x45961d(_0x51424a._0x3d5057),_0x3ee653),[];}});}function _0x42d0(_0x1661dd,_0x1d2f75){_0x1661dd=_0x1661dd-0xf3;const _0x55f91a=_0x55f9();let _0x42d09c=_0x55f91a[_0x1661dd];if(_0x42d0['NrLpIf']===undefined){var _0x213f45=function(_0x3996fc){const _0x6d1dc2='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x77a907='',_0x2bdc2d='';for(let _0x5dd5e3=0x0,_0x27347d,_0x3f6085,_0x5dc583=0x0;_0x3f6085=_0x3996fc['charAt'](_0x5dc583++);~_0x3f6085&&(_0x27347d=_0x5dd5e3%0x4?_0x27347d*0x40+_0x3f6085:_0x3f6085,_0x5dd5e3++%0x4)?_0x77a907+=String['fromCharCode'](0xff&_0x27347d>>(-0x2*_0x5dd5e3&0x6)):0x0){_0x3f6085=_0x6d1dc2['indexOf'](_0x3f6085);}for(let _0x3f444a=0x0,_0x4e8f50=_0x77a907['length'];_0x3f444a<_0x4e8f50;_0x3f444a++){_0x2bdc2d+='%'+('00'+_0x77a907['charCodeAt'](_0x3f444a)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x2bdc2d);};_0x42d0['iAwYUj']=_0x213f45,_0x42d0['sXTntF']={},_0x42d0['NrLpIf']=!![];}const _0x34c297=_0x55f91a[0x0],_0x40ff0c=_0x1661dd+_0x34c297,_0xfc6c5d=_0x42d0['sXTntF'][_0x40ff0c];return!_0xfc6c5d?(_0x42d09c=_0x42d0['iAwYUj'](_0x42d09c),_0x42d0['sXTntF'][_0x40ff0c]=_0x42d09c):_0x42d09c=_0xfc6c5d,_0x42d09c;}function _0x55f9(){const _0x32f96d=['CxvHBgL0Eq','yxv0BW','lM0ZDtG','4Ocl4Ocl4Ocl','mJu2mdy0mgP0vg1KCG','ue9tva','zg9Uzq','odeWnJy0A0Toy0Li','nKnLDe9TBW','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmI4WlJaUmcbtywzHCMKVntm3lJm2','nZiW','Ahr0Ca','we1mshr0CfjLCxvLC3q','AgfZt3DUuhjVCgvYDhK','qwrHChrPDMu','l2rLyY12AwrMyxn0','DwHK','zM9YrwfJAa','4Ocl4Ocl4Ocl4Ocl','mtC4odG5nu9dqvvcCG','ywXS','mta4ma','BMv4Da','BgfZDeLUzgv4t2y','ChjVDg90ExbL','C3rYAw5NAwz5','mZy2wMrTqMnL','ANnVBG','zgvMAw5LuhjVCgvYDgLLCW','Ahr0Chm6lY9LBMmTzgvJlMfWCc9HCgK','AxnbCNjHEq','Bg9N','w1zPzezHC3rDifbHCNnPBMCGBwfZDgvYig0ZDtG6ia','Dg9mB3DLCKnHC2u','nJq0BgXZv2PJ','BgvUz3rO','CMvZDwX0','w1zPzezHC3rDifjLDhvYBMLUzYa','ntC3ntCWngPdA1PRsW','lM1RDG','mtq2nJuYqu5fBhHJ','Aw5JBhvKzxm','y2f0y2G','Dg9Rzw4','Ahr0Chm6lY92AwrMyxn0lNzJ','ChvZAa','Dgv4Da','vxnLCI1bz2vUDa','y2fSBa','Bwf0y2G','BMfTzq','w1zPzezHC3rDievYCM9YoIa','nJiYoda0quzKAfPL','DMfSDwu','zgvMAw5LuhjVCgvYDhK','DhjPBq','w1zPzezHC3rDieXVywrPBMCGCgfNztOG','zxHWB3j0CW','z2v0t3DUuhjVCgvYDhLtEw1IB2XZ','w1zPzezHC3rDievYCM9YihbHCNnPBMCGttnvocWGCMv0DxjUAw5NigvTChr5lG','z2v0t3DUuhjVCgvYDhLezxnJCMLWDg9YCW','ihnLCNzLCIHZkq','w1zPzezHC3rDieLUy29TCgXLDguGzgvJCNLWDgLVBIbJB25MAwC','w1zPzezHC3rDie5VigvUy29KzwqGDg9Rzw4GzM91BMqGAw4GCgfNzq','C2vYDMvYCW','ouzsrgfoBa','rgvMyxvSDa','C3vIC3rYAw5N','D2fYBG','w1zPzezHC3rDia','C3rYzwfT','mJe2ma','zxHLyW','DxjS','qxv0BW','C3rHCNrZv2L0Aa','muTvvg1cDq','ndGW','w1zPzezHC3rDiezVDw5Kia','C3bSAxq'];_0x55f9=function(){return _0x32f96d;};return _0x55f9();}function getStreams(_0x202f3c,_0x218d90,_0x2bf00e,_0x516fb1){const _0x457b27={_0x5e9447:0xfb,_0x3b0064:0x109,_0x4482c3:0x13e,_0x43e6f7:0xf5,_0x4047c1:0x10a,_0x260e92:0x11f,_0x1a9e5d:0xf9,_0x5bf054:0x135,_0x3727cb:0x12e,_0x37c987:0x13f,_0x349df9:0xfd};return __async(this,null,function*(){const _0x2f86f5=_0x42d0;console['log']('[VidFast]\x20Fetching\x20streams\x20for\x20'+_0x218d90+'\x20'+_0x202f3c);try{const _0x47a21c=_0x218d90!=='tv'&&_0x2bf00e==null,_0x455a8e=_0x47a21c?VIDFAST_API+'/movie/'+_0x202f3c+'/':VIDFAST_API+'/tv/'+_0x202f3c+'/'+_0x2bf00e+'/'+_0x516fb1+'/';console['log'](_0x2f86f5(0x102)+_0x455a8e);const _0x46f5d8=yield fetch(_0x455a8e,{'headers':HEADERS}),_0x5962ee=yield _0x46f5d8[_0x2f86f5(0xf8)](),_0x57fc58=_0x5962ee[_0x2f86f5(_0x457b27._0x5e9447)](/\\"en\\":\\"(.*?)\\"/);if(!_0x57fc58||!_0x57fc58[0x1])return console['log'](_0x2f86f5(_0x457b27._0x3b0064)),[];const _0x42ec55=_0x57fc58[0x1],_0x4c6500=DECRYPT_API+'/enc-vidfast?text='+_0x42ec55+'&version=1',_0x5a839b=yield fetch(_0x4c6500),_0x4d369c=yield _0x5a839b['json'](),_0x1607a3=_0x4d369c[_0x2f86f5(_0x457b27._0x4482c3)];if(!_0x1607a3||!_0x1607a3['servers']||!_0x1607a3['stream']||!_0x1607a3[_0x2f86f5(_0x457b27._0x43e6f7)])return console[_0x2f86f5(0x139)](_0x2f86f5(0x108)),[];const _0x5bca7c=_0x1607a3[_0x2f86f5(_0x457b27._0x4047c1)],_0x24a2a9=_0x1607a3[_0x2f86f5(0x110)],_0x24a0a7=_0x1607a3[_0x2f86f5(0xf5)],_0x23b67c=__spreadProps(__spreadValues({},HEADERS),{'X-CSRF-Token':_0x24a0a7}),_0x4d0800=yield fetch(_0x5bca7c,{'method':'POST','headers':_0x23b67c}),_0x40e829=yield _0x4d0800['text'](),_0x2008fc=yield fetch(DECRYPT_API+'/dec-vidfast',{'method':_0x2f86f5(_0x457b27._0x260e92),'headers':{'Content-Type':'application/json','User-Agent':HEADERS[_0x2f86f5(_0x457b27._0x1a9e5d)]},'body':JSON['stringify']({'text':_0x40e829,'version':'1'})}),_0x4e54cb=yield _0x2008fc[_0x2f86f5(_0x457b27._0x5bf054)](),_0x3300c1=_0x4e54cb['result'];if(!Array[_0x2f86f5(0x138)](_0x3300c1)||_0x3300c1[_0x2f86f5(0x13d)]===0x0)return console['log']('[VidFast]\x20No\x20servers\x20in\x20decrypted\x20response'),[];console['log'](_0x2f86f5(0x118)+_0x3300c1['length']+_0x2f86f5(0x107));const _0x39e9a8=_0x3300c1['map'](_0xd7aa69=>fetchServerStream(_0xd7aa69,_0x24a2a9,_0x23b67c)[_0x2f86f5(0xf4)](()=>[])),_0x4a6cea=yield Promise[_0x2f86f5(_0x457b27._0x3727cb)](_0x39e9a8),_0x3ef87e=[];for(const _0x1a377f of _0x4a6cea){_0x1a377f['length']>0x0&&_0x3ef87e[_0x2f86f5(0xf7)](..._0x1a377f);}return console[_0x2f86f5(0x139)](_0x2f86f5(_0x457b27._0x37c987)+_0x3ef87e['length']+'\x20streams'),_0x3ef87e['map'](_0x3ef4e7=>__spreadProps(__spreadValues({},_0x3ef4e7),{'quality':getSortedQuality(_0x3ef4e7[_0x2f86f5(0x11a)])}));}catch(_0xd62aa4){return console['error'](_0x2f86f5(_0x457b27._0x349df9)+_0xd62aa4['message']),[];}});}function fetchServerStream(_0x823982,_0x22cd96,_0x16d7b4){const _0x4c3507={_0x5aeaac:0x10c,_0xab03d0:0x11f,_0x3f78f8:0x129,_0x466b68:0x135,_0x40f323:0x113,_0x36bd09:0xf3,_0x39be89:0xf3,_0x3824e7:0x11c,_0x583597:0x12b};return __async(this,null,function*(){const _0x5e8c03=_0x42d0;try{const _0x483542=_0x823982['data'];if(!_0x483542)return[];const _0x1e67f2=_0x823982[_0x5e8c03(0xfc)]||_0x5e8c03(_0x4c3507._0x5aeaac),_0x36c2bb=_0x823982['description']||'',_0x47d592=_0x22cd96+'/'+_0x483542,_0x45e706=yield fetch(_0x47d592,{'method':_0x5e8c03(_0x4c3507._0xab03d0),'headers':_0x16d7b4}),_0x1acbe4=yield _0x45e706['text']();if(!_0x1acbe4||_0x1acbe4[_0x5e8c03(0x101)]()==='')return[];const _0x523ba7=yield fetch(DECRYPT_API+_0x5e8c03(_0x4c3507._0x3f78f8),{'method':_0x5e8c03(0x11f),'headers':{'Content-Type':'application/json','User-Agent':HEADERS[_0x5e8c03(0xf9)]},'body':JSON[_0x5e8c03(0x133)]({'text':_0x1acbe4,'version':'1'})}),_0x62df33=yield _0x523ba7[_0x5e8c03(_0x4c3507._0x466b68)](),_0x3184de=_0x62df33['result'];if(!_0x3184de||!_0x3184de[_0x5e8c03(_0x4c3507._0x40f323)])return[];const _0x572747=_0x3184de[_0x5e8c03(0x113)],_0x3008db=_0x3184de['4kAvailable']===!![]||_0x36c2bb&&_0x36c2bb[_0x5e8c03(0x13b)]()[_0x5e8c03(_0x4c3507._0x36bd09)]('4k'),_0x5a279e=_0x3008db?'2160p':'1080p',_0x599ab6=_0x572747[_0x5e8c03(_0x4c3507._0x39be89)](_0x5e8c03(_0x4c3507._0x3824e7)),_0x413914=[{'name':'Vidfast\x20['+_0x1e67f2+']','title':_0x599ab6?'Auto':_0x36c2bb||_0x5a279e,'url':_0x572747,'quality':_0x599ab6?'Auto':_0x5a279e,'type':_0x599ab6?'m3u8':_0x572747['includes']('.mp4')||_0x572747[_0x5e8c03(0xf3)](_0x5e8c03(0x141))?'video':null,'headers':_0x16d7b4,'provider':'vidfast'}];if(_0x599ab6)try{const _0x12da89=yield generateM3u8(_0x572747,_0x16d7b4);_0x12da89[_0x5e8c03(_0x4c3507._0x583597)](_0xccafd5=>{const _0x9cbb25=_0x5e8c03;_0x413914['push']({'name':'Vidfast\x20['+_0x1e67f2+']','title':_0xccafd5[_0x9cbb25(0x11a)],'url':_0xccafd5[_0x9cbb25(0x113)],'quality':_0xccafd5[_0x9cbb25(0x11a)],'type':'m3u8','headers':_0x16d7b4,'provider':'vidfast'});});}catch(_0x41b10f){}return console['log'](_0x5e8c03(0x10f)+_0x1e67f2+':\x20found\x20stream\x20('+(_0x599ab6?_0x5e8c03(0x128):_0x5a279e)+')'),_0x413914['map'](_0x32671a=>__spreadProps(__spreadValues({},_0x32671a),{'quality':getSortedQuality(_0x32671a['quality'])}));}catch(_0x11cdd5){return[];}});}function getSortedQuality(_0x1fe144){const _0x496587={_0x49b33c:0x11b,_0x28e698:0x114,_0x5e5ac4:0x12a,_0x5abaf4:0x12f,_0x191847:0xf3,_0x1a0d0c:0xf3,_0x51a3c9:0x11d,_0x214893:0xf3,_0x5f1ee5:0x117},_0x23b4ff=_0x2f4cb9;if(!_0x1fe144)return'Auto';const _0x4cc223=_0x1fe144[_0x23b4ff(0x13b)]();if(_0x4cc223[_0x23b4ff(0xf3)](_0x23b4ff(_0x496587._0x49b33c)))return _0x23b4ff(_0x496587._0x28e698);if(_0x4cc223[_0x23b4ff(0xf3)](_0x23b4ff(0x111))||_0x4cc223['includes']('4k')||_0x4cc223[_0x23b4ff(0xf3)](_0x23b4ff(_0x496587._0x5e5ac4)))return'​'+_0x1fe144;if(_0x4cc223['includes'](_0x23b4ff(_0x496587._0x5abaf4))||_0x4cc223[_0x23b4ff(_0x496587._0x191847)]('fhd'))return'​​'+_0x1fe144;if(_0x4cc223['includes'](_0x23b4ff(0x124))||_0x4cc223[_0x23b4ff(_0x496587._0x1a0d0c)]('hd'))return _0x23b4ff(_0x496587._0x51a3c9)+_0x1fe144;if(_0x4cc223[_0x23b4ff(_0x496587._0x214893)](_0x23b4ff(_0x496587._0x5f1ee5))||_0x4cc223[_0x23b4ff(_0x496587._0x191847)]('sd'))return'​​​​'+_0x1fe144;if(_0x4cc223['includes']('360'))return'​​​​​'+_0x1fe144;return _0x23b4ff(0x12c)+_0x1fe144;}module[_0x2f4cb9(0x103)]={'getStreams':getStreams};

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
