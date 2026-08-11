const _0x4bb611=_0x15ba;(function(_0x53272e,_0x4f836d){const _0x51aaa9={_0x40bce7:0xb9,_0x1b8ec9:0xd4,_0x47b0b0:0xd0},_0x12f9ae=_0x15ba,_0x4d0bca=_0x53272e();while(!![]){try{const _0x56ef99=parseInt(_0x12f9ae(_0x51aaa9._0x40bce7))/0x1+-parseInt(_0x12f9ae(_0x51aaa9._0x1b8ec9))/0x2+parseInt(_0x12f9ae(0xd1))/0x3+parseInt(_0x12f9ae(0xf9))/0x4*(-parseInt(_0x12f9ae(0xed))/0x5)+-parseInt(_0x12f9ae(_0x51aaa9._0x47b0b0))/0x6*(parseInt(_0x12f9ae(0xd6))/0x7)+parseInt(_0x12f9ae(0xe8))/0x8+-parseInt(_0x12f9ae(0xf4))/0x9*(-parseInt(_0x12f9ae(0xe2))/0xa);if(_0x56ef99===_0x4f836d)break;else _0x4d0bca['push'](_0x4d0bca['shift']());}catch(_0x391ee3){_0x4d0bca['push'](_0x4d0bca['shift']());}}}(_0x3bbb,0x1f960));var __async=(_0x3201be,_0x47356b,_0x5aa756)=>{return new Promise((_0x14ddc2,_0x4f6472)=>{const _0x3fb712=_0x15ba;var _0x198337=_0x477364=>{try{_0x51e3f4(_0x5aa756['next'](_0x477364));}catch(_0x1535ed){_0x4f6472(_0x1535ed);}},_0x3758e1=_0x1bb98b=>{try{_0x51e3f4(_0x5aa756['throw'](_0x1bb98b));}catch(_0x114279){_0x4f6472(_0x114279);}},_0x51e3f4=_0x5a9902=>_0x5a9902[_0x3fb712(0xd9)]?_0x14ddc2(_0x5a9902[_0x3fb712(0xb1)]):Promise[_0x3fb712(0xaf)](_0x5a9902['value'])['then'](_0x198337,_0x3758e1);_0x51e3f4((_0x5aa756=_0x5aa756['apply'](_0x3201be,_0x47356b))['next']());});},cheerio=require('cheerio-without-node-native'),TMDB_API_KEY='1865f43a0549ca50d341dd9ab8b29f49',BASE_URL=_0x4bb611(0xe0),USER_AGENT=_0x4bb611(0xd3);function getTmdbInfo(_0x2c6410,_0x2668b5,_0x507ecc,_0x2885de){const _0x385ad5={_0x2f2dff:0xcb,_0x2e1e2c:0xcb,_0x2ac5b3:0xf0,_0x8e28d8:0xbe,_0x34ca4f:0xea,_0xa7efb0:0xb3,_0x50cf4a:0xca};return __async(this,null,function*(){const _0x4e03c4=_0x15ba,_0x4b1147=_0x2668b5==='tv'?'tv':'movie',_0x5374d6=Number[_0x4e03c4(_0x385ad5._0x2f2dff)](_0x507ecc)?_0x507ecc:0x1,_0x2c99e3=Number[_0x4e03c4(_0x385ad5._0x2e1e2c)](_0x2885de)?_0x2885de:0x1;try{if(_0x2668b5==='tv'){const _0x164a10='https://api.themoviedb.org/3/tv/'+_0x2c6410+'?api_key='+TMDB_API_KEY,_0x5d0f33=yield fetch(_0x164a10,{'headers':{'User-Agent':USER_AGENT,'Accept':'application/json'}});if(!_0x5d0f33['ok'])return{'title':'','year':null,'runtime':0x0};const _0xcaedb8=yield _0x5d0f33['json'](),_0x1f57be=_0xcaedb8['name']||'',_0x22eb13=_0xcaedb8[_0x4e03c4(0xa9)]?parseInt(_0xcaedb8['first_air_date']['slice'](0x0,0x4),0xa):null,_0x5ae794=_0x4e03c4(0xef)+_0x2c6410+'/season/'+_0x5374d6+'/episode/'+_0x2c99e3+'?api_key='+TMDB_API_KEY,_0x528a1c=yield fetch(_0x5ae794,{'headers':{'User-Agent':USER_AGENT,'Accept':_0x4e03c4(_0x385ad5._0x2ac5b3)}});let _0x447c00=_0xcaedb8[_0x4e03c4(0xb8)]?_0xcaedb8['episode_run_time'][0x0]:0x0;if(_0x528a1c['ok']){const _0x35eabd=yield _0x528a1c['json']();if(_0x35eabd['runtime'])_0x447c00=_0x35eabd[_0x4e03c4(0xc1)];}return{'title':_0x1f57be,'year':_0x22eb13,'runtime':_0x447c00};}else{const _0x18407a=_0x4e03c4(_0x385ad5._0x8e28d8)+_0x2c6410+_0x4e03c4(_0x385ad5._0x34ca4f)+TMDB_API_KEY,_0x375c05=yield fetch(_0x18407a,{'headers':{'User-Agent':USER_AGENT,'Accept':_0x4e03c4(_0x385ad5._0x2ac5b3)}});if(!_0x375c05['ok'])return{'title':'','year':null,'runtime':0x0};const _0x4cfc62=yield _0x375c05[_0x4e03c4(_0x385ad5._0xa7efb0)](),_0x3c4ede=_0x4cfc62[_0x4e03c4(0xb7)]?parseInt(_0x4cfc62[_0x4e03c4(0xb7)]['slice'](0x0,0x4),0xa):null;return{'title':_0x4cfc62[_0x4e03c4(_0x385ad5._0x50cf4a)]||'','year':_0x3c4ede,'runtime':_0x4cfc62['runtime']||0x0};}}catch(_0x213d24){return{'title':'','year':null,'runtime':0x0};}});}function normalize(_0x3736ac){const _0x5d5041={_0x3b7518:0xbd,_0x26707a:0xc2},_0x32ba83=_0x4bb611;return String(_0x3736ac||'')['toLowerCase']()[_0x32ba83(_0x5d5041._0x3b7518)](/[^a-z0-9]+/g,'\x20')[_0x32ba83(_0x5d5041._0x26707a)]();}function rankResults(_0x25b0ce,_0xe810ca){const _0x4c88b1={_0x206d9e:0xb0,_0x5c87fb:0xb0,_0x4cd509:0xda},_0x3874a0=_0x4bb611,_0x9ee06d=normalize(_0xe810ca),_0xbc5174=[],_0x32b90e=[];for(let _0x59c216=0x0;_0x59c216<_0x25b0ce[_0x3874a0(0xfa)];_0x59c216++){const _0x51a8fd=normalize(_0x25b0ce[_0x59c216]['title']);if(_0x51a8fd===_0x9ee06d)_0xbc5174[_0x3874a0(_0x4c88b1._0x206d9e)](_0x25b0ce[_0x59c216]);else{if(_0x51a8fd['indexOf'](_0x9ee06d)!==-0x1||_0x9ee06d['indexOf'](_0x51a8fd)!==-0x1)_0x32b90e[_0x3874a0(_0x4c88b1._0x5c87fb)](_0x25b0ce[_0x59c216]);}}return _0xbc5174[_0x3874a0(_0x4c88b1._0x4cd509)](_0x32b90e);}function absolutize(_0x26b9cc){const _0x21a207={_0x4e9df6:0xae,_0x10a1df:0xf3},_0x56fe15=_0x4bb611;if(!_0x26b9cc)return'';if(_0x26b9cc['indexOf'](_0x56fe15(_0x21a207._0x4e9df6))===0x0)return _0x26b9cc;if(_0x26b9cc[_0x56fe15(0xc6)]('//')===0x0)return _0x56fe15(_0x21a207._0x10a1df)+_0x26b9cc;if(_0x26b9cc['charAt'](0x0)==='/')return BASE_URL+_0x26b9cc;return BASE_URL+'/'+_0x26b9cc;}function searchSite(_0x54b77e){const _0x3c6cec={_0x360679:0xf1},_0x131591={_0xb64e89:0xdb,_0x40552d:0xaa,_0x151e34:0xf2,_0x3bda77:0xc2};return __async(this,null,function*(){const _0x104412=_0x15ba,_0x9fb706=[],_0x354c9d={};let _0x2109b2;try{const _0x2ff12a=yield fetch(BASE_URL+_0x104412(_0x3c6cec._0x360679)+encodeURIComponent(_0x54b77e),{'headers':{'User-Agent':USER_AGENT,'Accept':_0x104412(0xc4),'Accept-Language':_0x104412(0xb5)}});_0x2109b2=yield _0x2ff12a['text']();}catch(_0x2dcf28){return _0x9fb706;}const _0x446cd0=cheerio[_0x104412(0xcf)](_0x2109b2);return _0x446cd0(_0x104412(0xd2))['each'](function(_0x3a5c27,_0x377962){const _0x433d16=_0x104412,_0x2a78ff=absolutize(_0x446cd0(_0x377962)[_0x433d16(_0x131591._0xb64e89)]('href')||''),_0xa5e15a=(_0x446cd0(_0x377962)['attr']('title')||_0x446cd0(_0x377962)[_0x433d16(_0x131591._0x40552d)](_0x433d16(_0x131591._0x151e34))[_0x433d16(_0x131591._0xb64e89)](_0x433d16(0xf6))||'')[_0x433d16(_0x131591._0x3bda77)]();_0x2a78ff&&_0xa5e15a&&!_0x354c9d[_0x2a78ff]&&(_0x354c9d[_0x2a78ff]=!![],_0x9fb706['push']({'url':_0x2a78ff,'title':_0xa5e15a}));}),_0x9fb706;});}function getEpisodes(_0x1d5ecf){const _0x17cee0={_0x3974c9:0xcc,_0x183a8d:0xc9};return __async(this,null,function*(){const _0x30a83a=_0x15ba,_0x57c586=yield fetch(BASE_URL+_0x30a83a(0xb4)+_0x1d5ecf+'/episodes',{'headers':{'User-Agent':USER_AGENT,'X-Requested-With':_0x30a83a(_0x17cee0._0x3974c9)}}),_0x1de86c=yield _0x57c586[_0x30a83a(0xb3)]();return _0x1de86c&&_0x1de86c[_0x30a83a(_0x17cee0._0x183a8d)]?_0x1de86c[_0x30a83a(_0x17cee0._0x183a8d)]:[];});}function _0x3bbb(){const _0x1908b8=['l2fWAs9MCM9UDgvUzc9HBMLTzs8','zw4TvvmSzw47Ct0WlJK','Bwf0y2G','CMvSzwfZzv9KyxrL','zxbPC29Kzv9YDw5FDgLTzq','nZe0mgDUEgDuBG','l2fUAw1LlW','8j+oIYa','Dgv4Da','CMvWBgfJzq','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY9TB3zPzs8','w0fUAurcxsa','DxjS','CNvUDgLTzq','DhjPBq','iIbt','Dgv4Dc9ODg1SlgfWCgXPy2f0Aw9Ul3HODg1Sk3HTBcXHChbSAwnHDgLVBI94BwW7Ct0WlJKSkI8Qo3e9mc44','Cg9W','Aw5KzxHpzG','zxjYB3i','A29YzwfU','zxbPC29Kzxm','DgL0Bgu','AxnjBNrLz2vY','we1mshr0CfjLCxvLC3q','4PQHieHmuYb8iokpSE+4JYa','uKfxic8Gu1vc','Bg9Hza','nNLbzw5yCG','ndGZmZa5B2Lzv0Dd','ys5HBMLTzs1JyxjK','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYmc4WlJaUmcbtywzHCMKVntm3lJm2','mJaYnZuWA3PbB0Pe','BwvZC2fNzq','nJq4otqYEMnrtwnH','ihWG8j+tJcbbBMLeqIbtDhjLyw0','BgfUz3vHz2vZ','zg9Uzq','y29Uy2f0','yxr0CG','8j+hSpcFH7C','BMfTzq','AMfWyw5LC2u','8j+hUVcFH7G','Ahr0Chm6lY9HBMLKyI5HCha','l2fWAs9MCM9UDgvUzc9LCgLZB2rLlW','nJbhtMjVte0','EwvHCG','A29Y','ig1PBG','ywXS','zxHWB3j0CW','nZqZmtm2vuv0z25V','ihWG8j+uIIboyxrPDMu','p2fWAv9RzxK9','Aw5JBhvKzxm','zw1IzwrFDxjS','mJu4mJvxqxvIqLO','qw5PreiGFcbbDxrVihWG','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY90DI8','yxbWBgLJyxrPB24VANnVBG','l2jYB3DZzt9Xpq','Aw1N','Ahr0Chm6','mtG2nduZD0P2uKjY','rw5NBgLZAcbbDwrPBW','ywX0','y29Kzq','zw5NBgLZAa','ndH5weXKy1C','BgvUz3rO','zMLYC3rFywLYx2rHDgu','zMLUza','zw5N','8j+xO++4JW','ihn0CMvHBxm','Ahr0Ca','CMvZB2X2zq','ChvZAa','DMfSDwu','w0fUAurcxsbMB3vUzca','ANnVBG'];_0x3bbb=function(){return _0x1908b8;};return _0x3bbb();}function getLanguages(_0x465bf5,_0x353f32){const _0x1a5071={_0x441614:0xba,_0x5bdf7d:0xd8};return __async(this,null,function*(){const _0x24b7aa=_0x15ba,_0x3fd6ec=yield fetch(BASE_URL+_0x24b7aa(0xe1)+_0x465bf5+'/languages',{'headers':{'User-Agent':USER_AGENT,'X-Requested-With':'XMLHttpRequest','Referer':BASE_URL+_0x24b7aa(_0x1a5071._0x441614)+_0x353f32}}),_0x7fe0f0=yield _0x3fd6ec['json']();return _0x7fe0f0&&_0x7fe0f0[_0x24b7aa(_0x1a5071._0x5bdf7d)]?_0x7fe0f0[_0x24b7aa(0xd8)]:[];});}var HLS_REGEXES=[/file\s*:\s*["'](https?:\/\/[^"']+\.m3u8[^"']*)["']/i,/sources\s*:\s*\[\s*\{[^}]*file\s*:\s*["'](https?:\/\/[^"']+\.m3u8[^"']*)["']/i,/["'](https?:\/\/[^"']+\/master\.m3u8[^"']*)["']/i,/["'](https?:\/\/[^"']+\.m3u8[^"']*)["']/i];function extractEmbed(_0x24053c){const _0x5438e7={_0x10cf23:0xb6};return __async(this,null,function*(){const _0x5a4ab9=_0x15ba;try{const _0x378bcd=yield fetch(_0x24053c,{'headers':{'User-Agent':USER_AGENT,'Referer':BASE_URL+'/'}}),_0x4eba61=yield _0x378bcd[_0x5a4ab9(0xbc)]();for(let _0xa21305=0x0;_0xa21305<HLS_REGEXES['length'];_0xa21305++){const _0x2e03fd=_0x4eba61[_0x5a4ab9(_0x5438e7._0x10cf23)](HLS_REGEXES[_0xa21305]);if(_0x2e03fd&&_0x2e03fd[0x1])return _0x2e03fd[0x1];}}catch(_0x3f4868){}return null;});}function getStreams(_0xa7d540,_0x41060f,_0x37ec66,_0x45fdec){const _0x353538={_0x581c7c:0xbf,_0x5c10bd:0xc5,_0x210dd0:0xfa,_0x1bd778:0xec,_0xceeaae:0xe6,_0x3212c2:0xce,_0x4fdf11:0xeb,_0x501d83:0xab,_0x4ad37a:0xdf,_0xf6df98:0xdc,_0x2ee0f0:0xe3,_0xb6bc62:0xc1,_0x54cd17:0xc1,_0x44b1cd:0xe5,_0x54e52e:0xbb,_0x1eb1f3:0xe9,_0x506212:0xcd,_0x35e168:0xd7,_0x2432e2:0xb0,_0x1ae731:0xee,_0x5396f7:0xb2,_0x4c7641:0xc7,_0x19588f:0xd5};return __async(this,null,function*(){const _0x435279=_0x15ba;try{const _0x2988e6=yield getTmdbInfo(_0xa7d540,_0x41060f,_0x37ec66,_0x45fdec);if(!_0x2988e6[_0x435279(0xca)])return[];console['log'](_0x435279(_0x353538._0x581c7c)+_0x41060f+'\x20\x22'+_0x2988e6['title']+_0x435279(0xc3)+_0x37ec66+'E'+_0x45fdec);const _0xfb33e=rankResults(yield searchSite(_0x2988e6['title']),_0x2988e6['title']),_0x581036=_0x41060f==='tv'?_0x45fdec||0x1:0x1;for(let _0x1d692b=0x0;_0x1d692b<Math['min'](0x3,_0xfb33e['length']);_0x1d692b++){const _0x5c7b8d=_0xfb33e[_0x1d692b],_0xda1ce2=_0x5c7b8d[_0x435279(0xc0)]['split']('/')['filter'](Boolean)[_0x435279(0xc5)]()||'',_0x14918e=_0xda1ce2['split']('-')[_0x435279(_0x353538._0x5c10bd)](),_0xe5ca01=parseInt(_0x14918e,0xa);if(!_0xe5ca01)continue;let _0x119c32=[];try{_0x119c32=yield getEpisodes(_0xe5ca01);}catch(_0x32f686){continue;}if(!_0x119c32[_0x435279(_0x353538._0x210dd0)])continue;let _0xd170c2=null;for(let _0xd6c271=0x0;_0xd6c271<_0x119c32['length'];_0xd6c271++){if(_0x119c32[_0xd6c271]['number']===_0x581036){_0xd170c2=_0x119c32[_0xd6c271];break;}}if(!_0xd170c2)_0xd170c2=_0x119c32[_0x581036-0x1]||_0x119c32[0x0];if(!_0xd170c2||_0xd170c2['id']==null)continue;let _0x21a936=[];try{_0x21a936=yield getLanguages(_0xd170c2['id'],_0xda1ce2);}catch(_0x391440){continue;}const _0x34c2b3=[];for(let _0xfb51fa=0x0;_0xfb51fa<_0x21a936['length'];_0xfb51fa++){const _0x4cdccc=_0x21a936[_0xfb51fa][_0x435279(_0x353538._0x1bd778)];if(_0x4cdccc)_0x34c2b3['push']({'url':_0x4cdccc,'name':_0x21a936[_0xfb51fa][_0x435279(0xdd)]||_0x21a936[_0xfb51fa][_0x435279(0xf7)]||''});}if(!_0x34c2b3['length'])continue;const _0x8a1131=yield Promise[_0x435279(_0x353538._0xceeaae)](_0x34c2b3['map'](function(_0x3278ac){const _0x129cf5=_0x435279;return extractEmbed(_0x3278ac[_0x129cf5(0xc0)]);})),_0x39588e=[],_0x1eed04={};for(let _0x5da8e5=0x0;_0x5da8e5<_0x8a1131['length'];_0x5da8e5++){const _0x43d7a9=_0x8a1131[_0x5da8e5];if(!_0x43d7a9||_0x1eed04[_0x43d7a9])continue;_0x1eed04[_0x43d7a9]=!![];const _0x402a3e=String(_0x34c2b3[_0x5da8e5][_0x435279(0xdd)]||'')['toLowerCase']();let _0x3a031a=_0x34c2b3[_0x5da8e5][_0x435279(0xdd)]?_0x34c2b3[_0x5da8e5][_0x435279(0xdd)]:_0x435279(_0x353538._0x3212c2),_0x34c899=_0x435279(0xac),_0x481493='Subbed\x20/\x20Dubbed';if(_0x402a3e[_0x435279(_0x353538._0x4fdf11)](_0x435279(0xde))||_0x402a3e[_0x435279(0xeb)]('jp')||_0x402a3e[_0x435279(0xeb)]('jap'))_0x34c899='🇯🇵',_0x481493='Japanese\x20Audio';else{if(_0x402a3e['includes'](_0x435279(0xf8))||_0x402a3e['includes'](_0x435279(_0x353538._0x501d83))||_0x402a3e[_0x435279(0xeb)]('en'))_0x34c899=_0x435279(_0x353538._0x4ad37a),_0x481493=_0x435279(0xf5);else(_0x402a3e['includes'](_0x435279(0xc8))||_0x402a3e[_0x435279(0xeb)](_0x435279(0xe4))||_0x402a3e['includes']('kr'))&&(_0x34c899=_0x435279(_0x353538._0xf6df98),_0x481493='Korean\x20Audio');}const _0x33e2de=_0x2988e6[_0x435279(_0x353538._0x2ee0f0)]?'\x20('+_0x2988e6[_0x435279(_0x353538._0x2ee0f0)]+')':'';let _0x4e63e3='N/A';_0x2988e6[_0x435279(_0x353538._0xb6bc62)]&&Number['isInteger'](_0x2988e6['runtime'])&&_0x2988e6[_0x435279(0xc1)]>0x0&&(_0x4e63e3=_0x2988e6[_0x435279(_0x353538._0x54cd17)]+_0x435279(_0x353538._0x44b1cd));var _0x2a4dc5=_0x435279(_0x353538._0x54e52e)+_0x2988e6[_0x435279(0xca)]+_0x33e2de,_0x5191ff='🏷️\x20Auto\x20|\x20'+_0x34c899+'\x20'+_0x3a031a+_0x435279(_0x353538._0x1eb1f3),_0x1f71d8=_0x435279(_0x353538._0x506212)+_0x4e63e3+_0x435279(_0x353538._0x35e168),_0x159785=_0x2a4dc5+'\x0a'+_0x5191ff+'\x0a'+_0x1f71d8;_0x39588e[_0x435279(_0x353538._0x2432e2)]({'name':_0x435279(_0x353538._0x1ae731)+_0x481493,'title':_0x159785,'url':_0x43d7a9,'quality':'Auto','description':_0x159785,'headers':{'Referer':BASE_URL+'/'}});}if(_0x39588e[_0x435279(0xfa)])return console['log'](_0x435279(_0x353538._0x5396f7)+_0x39588e['length']+_0x435279(0xad)),_0x39588e;}return console['log']('[AniDB]\x20no\x20streams\x20found'),[];}catch(_0x3c169f){return console[_0x435279(_0x353538._0x4c7641)]('[AniDB]\x20Fatal:\x20'+(_0x3c169f&&_0x3c169f[_0x435279(_0x353538._0x19588f)])),[];}});}function _0x15ba(_0x51578c,_0x1550cf){_0x51578c=_0x51578c-0xa9;const _0x3bbb14=_0x3bbb();let _0x15bafa=_0x3bbb14[_0x51578c];if(_0x15ba['SGTBeU']===undefined){var _0x1ec826=function(_0x2eef8d){const _0x460336='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x3201be='',_0x47356b='';for(let _0x5aa756=0x0,_0x14ddc2,_0x4f6472,_0x198337=0x0;_0x4f6472=_0x2eef8d['charAt'](_0x198337++);~_0x4f6472&&(_0x14ddc2=_0x5aa756%0x4?_0x14ddc2*0x40+_0x4f6472:_0x4f6472,_0x5aa756++%0x4)?_0x3201be+=String['fromCharCode'](0xff&_0x14ddc2>>(-0x2*_0x5aa756&0x6)):0x0){_0x4f6472=_0x460336['indexOf'](_0x4f6472);}for(let _0x3758e1=0x0,_0x51e3f4=_0x3201be['length'];_0x3758e1<_0x51e3f4;_0x3758e1++){_0x47356b+='%'+('00'+_0x3201be['charCodeAt'](_0x3758e1)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x47356b);};_0x15ba['LYydZP']=_0x1ec826,_0x15ba['hvANvm']={},_0x15ba['SGTBeU']=!![];}const _0x55e8e9=_0x3bbb14[0x0],_0x41789c=_0x51578c+_0x55e8e9,_0x1b4f0c=_0x15ba['hvANvm'][_0x41789c];return!_0x1b4f0c?(_0x15bafa=_0x15ba['LYydZP'](_0x15bafa),_0x15ba['hvANvm'][_0x41789c]=_0x15bafa):_0x15bafa=_0x1b4f0c,_0x15bafa;}module[_0x4bb611(0xe7)]={'getStreams':getStreams};

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
