var _0x4d7322=_0x5931;(function(_0x274395,_0x42d5c2){var _0x5a6e0b={_0x535452:0x236,_0x3f0ba1:0x204,_0x449d58:0x23f,_0x246868:0x201,_0x58f74c:0x1ed},_0x1fad9e=_0x5931,_0x45ac1a=_0x274395();while(!![]){try{var _0x159651=-parseInt(_0x1fad9e(0x1ee))/0x1*(parseInt(_0x1fad9e(0x200))/0x2)+parseInt(_0x1fad9e(_0x5a6e0b._0x535452))/0x3+-parseInt(_0x1fad9e(_0x5a6e0b._0x3f0ba1))/0x4*(parseInt(_0x1fad9e(0x207))/0x5)+parseInt(_0x1fad9e(0x228))/0x6+parseInt(_0x1fad9e(0x21d))/0x7*(-parseInt(_0x1fad9e(_0x5a6e0b._0x449d58))/0x8)+-parseInt(_0x1fad9e(_0x5a6e0b._0x246868))/0x9+parseInt(_0x1fad9e(_0x5a6e0b._0x58f74c))/0xa*(parseInt(_0x1fad9e(0x21b))/0xb);if(_0x159651===_0x42d5c2)break;else _0x45ac1a['push'](_0x45ac1a['shift']());}catch(_0x21869f){_0x45ac1a['push'](_0x45ac1a['shift']());}}}(_0x27f4,0x21116));var __async=(_0x17326d,_0x3bf1f8,_0x9587a8)=>{return new Promise((_0x370d04,_0x1b7722)=>{var _0x10c202=_0x5931,_0x4088dc=_0x43429a=>{try{_0x259de0(_0x9587a8['next'](_0x43429a));}catch(_0x54d9d2){_0x1b7722(_0x54d9d2);}},_0x157564=_0x54cc36=>{var _0x34a148=_0x5931;try{_0x259de0(_0x9587a8[_0x34a148(0x239)](_0x54cc36));}catch(_0x41b979){_0x1b7722(_0x41b979);}},_0x259de0=_0x1f9f9b=>_0x1f9f9b[_0x10c202(0x234)]?_0x370d04(_0x1f9f9b[_0x10c202(0x235)]):Promise[_0x10c202(0x230)](_0x1f9f9b['value'])['then'](_0x4088dc,_0x157564);_0x259de0((_0x9587a8=_0x9587a8[_0x10c202(0x208)](_0x17326d,_0x3bf1f8))['next']());});},PROVIDER_NAME=_0x4d7322(0x1e8),DESIFLIX_BASE='https://manifest.desitvhub.eu.org',TMDB_API_KEY='439c478a771f35c05022f9feabcca01c',FETCH_TIMEOUT=0x2ee0,USER_AGENT=_0x4d7322(0x222);function log(_0x59bee8){console['log']('['+PROVIDER_NAME+']\x20'+_0x59bee8);}function err(_0x5738fe){var _0x222701={_0x243566:0x23d},_0x4244da=_0x4d7322;console[_0x4244da(_0x222701._0x243566)]('['+PROVIDER_NAME+']\x20'+_0x5738fe);}function _0x5931(_0x231e7e,_0x4320d7){_0x231e7e=_0x231e7e-0x1e5;var _0x27f487=_0x27f4();var _0x5931a0=_0x27f487[_0x231e7e];if(_0x5931['ivjWSM']===undefined){var _0x285f6b=function(_0x39a065){var _0x7b51e2='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';var _0x17326d='',_0x3bf1f8='';for(var _0x9587a8=0x0,_0x370d04,_0x1b7722,_0x4088dc=0x0;_0x1b7722=_0x39a065['charAt'](_0x4088dc++);~_0x1b7722&&(_0x370d04=_0x9587a8%0x4?_0x370d04*0x40+_0x1b7722:_0x1b7722,_0x9587a8++%0x4)?_0x17326d+=String['fromCharCode'](0xff&_0x370d04>>(-0x2*_0x9587a8&0x6)):0x0){_0x1b7722=_0x7b51e2['indexOf'](_0x1b7722);}for(var _0x157564=0x0,_0x259de0=_0x17326d['length'];_0x157564<_0x259de0;_0x157564++){_0x3bf1f8+='%'+('00'+_0x17326d['charCodeAt'](_0x157564)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x3bf1f8);};_0x5931['tOfbOo']=_0x285f6b,_0x5931['gSBcIf']={},_0x5931['ivjWSM']=!![];}var _0x2de63d=_0x27f487[0x0],_0x1837e9=_0x231e7e+_0x2de63d,_0x2c12f1=_0x5931['gSBcIf'][_0x1837e9];return!_0x2c12f1?(_0x5931a0=_0x5931['tOfbOo'](_0x5931a0),_0x5931['gSBcIf'][_0x1837e9]=_0x5931a0):_0x5931a0=_0x2c12f1,_0x5931a0;}function raceTimeout(_0x31afe2){var _0x49ec66={_0x331f6b:0x1e6};return new Promise(function(_0x256f83,_0x3b6322){setTimeout(function(){var _0x44c5ad=_0x5931;_0x3b6322(new Error(_0x44c5ad(_0x49ec66._0x331f6b)+_0x31afe2+'ms'));},_0x31afe2);});}function fetchJson(_0x568905){var _0x986e8e={_0x3b2ab1:0x1f4,_0x291655:0x205};return __async(this,null,function*(){var _0x1d0b41=_0x5931;try{var _0x4f618d=fetch(_0x568905,{'headers':{'User-Agent':USER_AGENT,'Accept':_0x1d0b41(0x215)}}),_0x3a7a18=yield Promise['race']([_0x4f618d,raceTimeout(FETCH_TIMEOUT)]);if(_0x3a7a18&&_0x3a7a18['ok'])return yield _0x3a7a18[_0x1d0b41(_0x986e8e._0x3b2ab1)]();}catch(_0x365175){err('fetch\x20failed:\x20'+_0x568905+_0x1d0b41(_0x986e8e._0x291655)+(_0x365175['message']||''));}return null;});}function _0x27f4(){var _0x2b69a5=['ihr5Cgu9','mZG5mZzNz0X6t3G','tva0','BwfSyxLHBgfT','vgLTzw91Dca','l3n0CMvHBs9ZzxjPzxmV','rgvZAuzSAxG','D2vICMLW','C3bSAxq','p2fWAv9RzxK9','zxH0zxjUywXvCMW','mJbbCfflr0C','mZC0vw1IywjQ','mJe2mha','ihm9','C29YDa','ihWG8j+sVIa','DxjS','ANnVBG','Agv2yW','uMvXDwvZDdOGDg1KyKLKpq','EwvHCG','nZiWCa','qufd','8j+tPsbxruiTreW','rg9SyNKGvMLZAw9U','ihWG8j+tPIa','lM1Wna','Edi2nq','zgrWiduUmq','mte4r3b5D1ft','mtCYodCYow9NCevwrq','ChvZAa','BMfTzq','ntzXrNvzzLG','ic0+ia','rw5NBgLZAa','nJm3nJvgBe1AsKq','yxbWBhK','DgvSDwD1','mta4ma','ndGWCa','Aw1KyL9Pza','vgvSDwD1','zMLYC3rFywLYx2rHDgu','BgvUz3rO','Dg9mB3DLCKnHC2u','ndGW','mJe2ma','mta4mha','Adi2nq','yxbWBgLJyxrPB24VANnVBG','AgrYAxa','Dhj1zwHK','nY4X','8j+oPsa','t3jPz2LUywW','mZqXmZeZnxHTAwLXBq','lMPZB24','mJu5BKjRteDt','ihWG8j+mIca','CgfKu3rHCNq','8j+sVYbcBhvsyxK','zg9SyNKGDMLZAw9U','tw96AwXSys81lJaGkfDPBMrVD3mGtLqGmtaUmdSGv2LUnJq7ihG2ncKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeYnc4WlJaUmcbtywzHCMKVntm3lJm2','sevwqYb4mJy0','tM8GC3rYzwfTCYbYzxr1CM5LzcbMCM9TierLC2LgBgL4','AgrY','igu9','8j+nVYa','mZaZnZq0wuXryLPf','zxH0zxjUywXFAwrZ','vhj1zuHe','zgq1lJe','vgfTAwW','Aw1KyKLK','ihWG8j+oPYa','ihnVCNrLzcbZDhjLyw1Z','CMvZB2X2zq','rgvZAuzSAxGGvgL0Bgu','DgL0Bgu','ihWG8j+uIIa','zg9Uzq','DMfSDwu','mteXmdyWzfLHDMT3','DgfTAwW','sevwqYb4mJy1','DgHYB3C','zw5NBgLZAa','C3rYzwfTCW','Aw5KzxHpzG','zxjYB3i'];_0x27f4=function(){return _0x2b69a5;};return _0x27f4();}function getTMDBDetails(_0xecda0e,_0x24c07e){var _0x21122e={_0x1e2887:0x1eb,_0x59edc8:0x231,_0x49ad48:0x20e,_0x27b1c1:0x1ea,_0x556d57:0x229,_0x47c6de:0x20c};return __async(this,null,function*(){var _0x35b860=_0x5931,_0x259e30=_0x24c07e==='tv'||_0x24c07e==='series',_0x482a5c=_0x259e30?'tv':'movie',_0x40b2a9='https://api.themoviedb.org/3/'+_0x482a5c+'/'+_0xecda0e+_0x35b860(_0x21122e._0x1e2887)+TMDB_API_KEY+'&append_to_response=external_ids',_0x12ce82=yield fetchJson(_0x40b2a9);if(!_0x12ce82)return{'title':'DesiFlix\x20Title','year':'','imdbId':null};return{'title':(_0x259e30?_0x12ce82['name']:_0x12ce82[_0x35b860(0x232)])||_0x35b860(_0x21122e._0x59edc8),'year':(_0x259e30?_0x12ce82[_0x35b860(_0x21122e._0x49ad48)]||'':_0x12ce82['release_date']||'')[_0x35b860(_0x21122e._0x27b1c1)]('-')[0x0],'imdbId':_0x12ce82['imdb_id']||_0x12ce82[_0x35b860(_0x21122e._0x556d57)]&&_0x12ce82[_0x35b860(0x229)][_0x35b860(_0x21122e._0x47c6de)]||null};});}function parseLanguage(_0x5efffd){var _0x9cda3f={_0x439681:0x23c,_0x1c2964:0x23a,_0x40cd7d:0x206,_0x409340:0x237,_0x110108:0x23c},_0x265e8b=_0x4d7322;if(_0x5efffd[_0x265e8b(_0x9cda3f._0x439681)]('multi')!==-0x1)return'Multi-Audio';var _0x421a93=_0x5efffd['indexOf'](_0x265e8b(_0x9cda3f._0x1c2964))!==-0x1||_0x5efffd['indexOf']('eng')!==-0x1,_0x2d30d3=_0x5efffd['indexOf']('hindi')!==-0x1||_0x5efffd[_0x265e8b(0x23c)]('hin')!==-0x1;if(_0x421a93&&_0x2d30d3||_0x5efffd[_0x265e8b(_0x9cda3f._0x439681)]('dual')!==-0x1)return'Dual-Audio';if(_0x2d30d3)return'Hindi';if(_0x421a93)return _0x265e8b(_0x9cda3f._0x40cd7d);if(_0x5efffd['indexOf'](_0x265e8b(_0x9cda3f._0x409340))!==-0x1)return _0x265e8b(0x22c);if(_0x5efffd[_0x265e8b(_0x9cda3f._0x110108)](_0x265e8b(0x209))!==-0x1)return _0x265e8b(0x20d);if(_0x5efffd['indexOf'](_0x265e8b(0x1e5))!==-0x1)return'Malayalam';if(_0x5efffd['indexOf']('kannada')!==-0x1)return'Kannada';return _0x265e8b(0x21a);}function buildDropdownMetadata(_0x3da196,_0x32fbf3,_0x103e2a,_0x4c6362,_0xae78a2,_0x229e52){var _0x1614b3={_0x3b03c9:0x231,_0x34bb7b:0x1f7,_0x18b68a:0x203,_0x3f9fbc:0x210,_0x11b24c:0x21f,_0x4f7c0d:0x212,_0x42d51e:0x23c,_0x3265d0:0x233,_0x9260b1:0x1f5,_0x5595df:0x1fe,_0x3fcd32:0x238,_0x5cfc99:0x214,_0x4876fc:0x1fe,_0x284eed:0x1ff,_0x589648:0x22a,_0x10985f:0x219,_0x2ce49b:0x22e,_0x22dac6:0x1fa,_0x59c289:0x23c,_0x5014cc:0x23c,_0x1455c5:0x240,_0x33f56f:0x23c,_0x51cd1f:0x225,_0x349993:0x23c,_0x2db75e:0x221,_0x39eb40:0x1fc},_0x45e741=_0x4d7322,_0x2c722e=_0x3da196['title']||_0x45e741(_0x1614b3._0x3b03c9),_0x146dbe=_0x3da196['year']?'\x20('+_0x3da196[_0x45e741(_0x1614b3._0x34bb7b)]+')':'',_0x5dee21=(_0x229e52[_0x45e741(0x232)]||'')+'\x20'+(_0x229e52[_0x45e741(_0x1614b3._0x18b68a)]||'')+'\x20'+(_0x229e52['url']||''),_0x4bc44d=_0x5dee21[_0x45e741(_0x1614b3._0x3f9fbc)](),_0x59c9bb=_0x45e741(0x227)+_0x2c722e+_0x146dbe;_0x103e2a&&_0x4c6362!=null&&_0xae78a2!=null&&(_0x59c9bb+='\x20|\x20S'+String(_0x4c6362)[_0x45e741(_0x1614b3._0x11b24c)](0x2,'0')+'E'+String(_0xae78a2)[_0x45e741(0x21f)](0x2,'0'));var _0x1abd08='💎';if(_0x32fbf3['indexOf'](_0x45e741(_0x1614b3._0x4f7c0d))!==-0x1||_0x32fbf3[_0x45e741(_0x1614b3._0x42d51e)]('4k')!==-0x1)_0x1abd08='🌟';else{if(_0x32fbf3['indexOf'](_0x45e741(0x20a))!==-0x1)_0x1abd08='🔥';}var _0xa6bb03=parseLanguage(_0x4bc44d),_0x573257=_0x4bc44d['match'](/(\d+(?:\.\d+)?\s*(?:gb|mb))/i),_0x2dac7d=_0x573257?_0x573257[0x1]['toUpperCase']():'Variable\x20Size',_0x430b04=_0x1abd08+'\x20'+_0x32fbf3+_0x45e741(0x1f2)+_0x2dac7d+_0x45e741(_0x1614b3._0x3265d0)+_0xa6bb03,_0x261585='x264';if(_0x4bc44d['indexOf'](_0x45e741(_0x1614b3._0x9260b1))!==-0x1&&(_0x4bc44d['indexOf'](_0x45e741(_0x1614b3._0x5595df))!==-0x1||_0x4bc44d['indexOf'](_0x45e741(0x214))!==-0x1))_0x261585=_0x45e741(_0x1614b3._0x3fcd32);else{if(_0x4bc44d['indexOf'](_0x45e741(_0x1614b3._0x9260b1))!==-0x1)_0x261585=_0x45e741(0x223);else(_0x4bc44d[_0x45e741(_0x1614b3._0x42d51e)](_0x45e741(0x1fe))!==-0x1||_0x4bc44d[_0x45e741(0x23c)](_0x45e741(_0x1614b3._0x5cfc99))!==-0x1)&&(_0x261585=_0x45e741(_0x1614b3._0x4876fc));}var _0x176bed=_0x45e741(0x1f9);if(_0x4bc44d['indexOf']('ddp5.1')!==-0x1||_0x4bc44d['indexOf'](_0x45e741(_0x1614b3._0x284eed))!==-0x1)_0x176bed='DDP5.1';else{if(_0x4bc44d['indexOf'](_0x45e741(0x22b))!==-0x1||_0x4bc44d['indexOf']('5.1')!==-0x1)_0x176bed='DD5.1';else{if(_0x4bc44d[_0x45e741(0x23c)](_0x45e741(0x218))!==-0x1)_0x176bed='7.1';else{if(_0x4bc44d['indexOf'](_0x45e741(0x217))!==-0x1)_0x176bed=_0x45e741(_0x1614b3._0x589648);}}}var _0x4cf26b=_0x4bc44d[_0x45e741(0x23c)]('atmos')!==-0x1?'\x20|\x20🔊\x20Atmos':'',_0x4831c7=_0x45e741(_0x1614b3._0x10985f)+_0x261585+_0x45e741(_0x1614b3._0x2ce49b)+_0x176bed+_0x4cf26b,_0x2f930f=_0x45e741(_0x1614b3._0x22dac6);if(_0x4bc44d['indexOf']('web-rip')!==-0x1||_0x4bc44d[_0x45e741(_0x1614b3._0x42d51e)](_0x45e741(0x1e9))!==-0x1)_0x2f930f='🌐\x20WEB-RIP';else{if(_0x4bc44d[_0x45e741(_0x1614b3._0x42d51e)]('bluray')!==-0x1)_0x2f930f=_0x45e741(0x220);else{if(_0x4bc44d[_0x45e741(_0x1614b3._0x59c289)](_0x45e741(0x216))!==-0x1)_0x2f930f='📺\x20HD-RIP';}}var _0x83022b=_0x229e52['url']&&_0x229e52['url'][_0x45e741(_0x1614b3._0x5014cc)](_0x45e741(0x1fd))!==-0x1?_0x45e741(_0x1614b3._0x1455c5):'MKV',_0x4fac72='SDR';if(_0x4bc44d['indexOf']('10bit')!==-0x1||_0x4bc44d[_0x45e741(_0x1614b3._0x33f56f)]('10-bit')!==-0x1)_0x4fac72=_0x4bc44d[_0x45e741(0x23c)](_0x45e741(_0x1614b3._0x51cd1f))!==-0x1?'10bit\x20HDR':'10bit';else{if(_0x4bc44d['indexOf']('hdr10+')!==-0x1)_0x4fac72='HDR10+';else{if(_0x4bc44d[_0x45e741(0x23c)]('hdr')!==-0x1)_0x4fac72='HDR';else(_0x4bc44d['indexOf']('dv')!==-0x1||_0x4bc44d[_0x45e741(_0x1614b3._0x349993)](_0x45e741(_0x1614b3._0x2db75e))!==-0x1)&&(_0x4fac72=_0x45e741(0x1fb));}}var _0x18afa2=_0x2f930f+_0x45e741(_0x1614b3._0x39eb40)+_0x83022b+_0x45e741(0x21e)+_0x4fac72,_0x30e4f1='📎\x20'+PROVIDER_NAME;return _0x59c9bb+'\x0a'+_0x430b04+'\x0a'+_0x4831c7+'\x0a'+_0x18afa2+'\x0a'+_0x30e4f1;}function getStreams(_0x151035,_0x1d5d5f,_0x4a4a6f,_0xe39a47){var _0x1d3ba2={_0x376f8b:0x23e,_0x3e88d4:0x226,_0x234014:0x23b,_0x5f2b9a:0x224,_0x5036b8:0x1f3,_0x5a64b4:0x1ec,_0xe7a027:0x232,_0x537b91:0x202},_0x2bcd9a={_0x3f06da:0x203},_0x29df05={_0x448346:0x23c,_0x266da8:0x23c};return __async(this,null,function*(){var _0x2cbeaf=_0x5931,_0x30b586=_0x1d5d5f==='tv'||_0x1d5d5f==='series';log(_0x2cbeaf(0x1f6)+_0x151035+_0x2cbeaf(_0x1d3ba2._0x376f8b)+_0x1d5d5f+_0x2cbeaf(0x1f0)+_0x4a4a6f+_0x2cbeaf(_0x1d3ba2._0x3e88d4)+_0xe39a47);var _0x21d9e5=yield getTMDBDetails(_0x151035,_0x1d5d5f),_0xcfc11=_0x21d9e5['imdbId']||_0x151035,_0x5e2034='';if(_0x30b586){var _0x8318cb=_0x4a4a6f!=null?_0x4a4a6f:0x1,_0x476b1f=_0xe39a47!=null?_0xe39a47:0x1;_0x5e2034=DESIFLIX_BASE+'/stream/series/'+_0xcfc11+':'+_0x8318cb+':'+_0x476b1f+'.json';}else _0x5e2034=DESIFLIX_BASE+'/stream/movie/'+_0xcfc11+_0x2cbeaf(0x21c);log('Fetching\x20streams\x20from:\x20'+_0x5e2034);var _0x1ff470=yield fetchJson(_0x5e2034);if((!_0x1ff470||!_0x1ff470[_0x2cbeaf(0x23b)]||!_0x1ff470[_0x2cbeaf(0x23b)]['length'])&&_0x21d9e5[_0x2cbeaf(0x22d)]){var _0x11e4d1=_0x30b586?DESIFLIX_BASE+_0x2cbeaf(0x1e7)+_0x151035+':'+(_0x4a4a6f||0x1)+':'+(_0xe39a47||0x1)+'.json':DESIFLIX_BASE+'/stream/movie/'+_0x151035+'.json';log('Retrying\x20with\x20fallback\x20endpoint:\x20'+_0x11e4d1),_0x1ff470=yield fetchJson(_0x11e4d1);}if(!_0x1ff470||!_0x1ff470[_0x2cbeaf(0x23b)]||!_0x1ff470[_0x2cbeaf(_0x1d3ba2._0x234014)][_0x2cbeaf(0x20f)])return log(_0x2cbeaf(_0x1d3ba2._0x5f2b9a)),[];var _0x143585=[],_0x4c94ec={};for(var _0x217402=0x0;_0x217402<_0x1ff470[_0x2cbeaf(_0x1d3ba2._0x234014)]['length'];_0x217402++){var _0x2af0ce=_0x1ff470['streams'][_0x217402],_0x336fb5=_0x2af0ce[_0x2cbeaf(_0x1d3ba2._0x5036b8)]||_0x2af0ce[_0x2cbeaf(_0x1d3ba2._0x5a64b4)];if(!_0x336fb5||_0x4c94ec[_0x336fb5])continue;_0x4c94ec[_0x336fb5]=!![];var _0x387647=((_0x2af0ce[_0x2cbeaf(_0x1d3ba2._0xe7a027)]||'')+'\x20'+(_0x2af0ce['name']||'')+'\x20'+_0x336fb5)['toLowerCase'](),_0xf21667='1080p';if(_0x387647[_0x2cbeaf(0x23c)]('2160')!==-0x1||_0x387647['indexOf']('4k')!==-0x1)_0xf21667=_0x2cbeaf(0x1ef);else{if(_0x387647['indexOf']('720')!==-0x1)_0xf21667='720p';else{if(_0x387647[_0x2cbeaf(0x23c)](_0x2cbeaf(0x211))!==-0x1)_0xf21667='480p';}}var _0x5c0eb6=parseLanguage(_0x387647),_0x2ae4a4=buildDropdownMetadata(_0x21d9e5,_0xf21667,_0x30b586,_0x4a4a6f,_0xe39a47,_0x2af0ce);_0x143585[_0x2cbeaf(_0x1d3ba2._0x537b91)]({'name':PROVIDER_NAME+'\x20|\x20'+_0xf21667+'\x20|\x20'+_0x5c0eb6,'title':_0x2ae4a4,'size':_0x2ae4a4,'description':_0x2ae4a4,'url':_0x336fb5,'quality':'','language':'','headers':{'User-Agent':USER_AGENT,'Referer':DESIFLIX_BASE+'/'}});}function _0x413fb1(_0x2c8dd3){var _0x59eef5=_0x2cbeaf,_0x5af0d2=_0x2c8dd3['toLowerCase']();if(_0x5af0d2[_0x59eef5(_0x29df05._0x448346)]('2160p')!==-0x1||_0x5af0d2[_0x59eef5(0x23c)]('4k')!==-0x1)return 0x870;if(_0x5af0d2[_0x59eef5(_0x29df05._0x266da8)](_0x59eef5(0x213))!==-0x1)return 0x438;if(_0x5af0d2['indexOf'](_0x59eef5(0x1f8))!==-0x1)return 0x2d0;if(_0x5af0d2[_0x59eef5(_0x29df05._0x266da8)](_0x59eef5(0x20b))!==-0x1)return 0x1e0;return 0x0;}return _0x143585[_0x2cbeaf(0x1f1)](function(_0x44ed16,_0x240b31){var _0x373e3e=_0x2cbeaf;return _0x413fb1(_0x240b31['name'])-_0x413fb1(_0x44ed16[_0x373e3e(_0x2bcd9a._0x3f06da)]);}),log('Returning\x20'+_0x143585['length']+_0x2cbeaf(0x22f)),_0x143585;});}typeof module!=='undefined'&&module['exports']?module['exports']={'getStreams':getStreams}:global['getStreams']=getStreams;
/* NUVIO_TV_DIRECT_MEDIA_V2:2a707a65dbcc */
;(function(g,c){"use strict";
var ASSET=/\.(?:woff2?|ttf|otf|eot|css|js|mjs|map|png|jpe?g|gif|svg|ico|webmanifest|json|xml|vtt|srt)(?:[?#]|$)/i;
var DEMO=/(?:chrome\/static\/videos|sticky\/videos|static\/money|grok-|radar_promo|big[_-]?buck[_-]?bunny|sample[-_]?videos|test-videos)/i;
var SOCIAL=/(?:^|\.)(?:twitter\.com|x\.com|twimg\.com|google\.com|googleusercontent\.com|gitlab\.com|github\.com|facebook\.com|instagram\.com)$/i;
function s(v){return String(v==null?"":v).replace(/[\u200B-\u200D\uFEFF]/g,"").trim()}
function clean(v){return s(v).replace(/&amp;|&#038;/gi,"&").replace(/\\\//g,"/").replace(/\\u0026/gi,"&").replace(/\\u003d/gi,"=").replace(/\\x2f/gi,"/")}
function abs(v,b){try{return new URL(clean(v),b).toString()}catch(_){return ""}}
function hostname(u){try{return new URL(u).hostname.toLowerCase()}catch(_){return ""}}
function origin(u){try{return new URL(u).origin}catch(_){return ""}}
function rejected(u){var h=hostname(u);if(!h||ASSET.test(u)||DEMO.test(u)||SOCIAL.test(h))return true;for(var i=0;i<c.blockedHosts.length;i++)if(h===c.blockedHosts[i]||h.endsWith("."+c.blockedHosts[i]))return true;return false}
function timeout(){try{return typeof AbortSignal!=="undefined"&&AbortSignal.timeout?AbortSignal.timeout(c.timeoutMs):undefined}catch(_){return undefined}}
function headers(base,ref,target){var out={};if(base&&typeof base==="object")Object.keys(base).forEach(function(k){out[k]=s(base[k])});if(ref&&!out.Referer&&!out.referer)out.Referer=ref;var o=origin(ref||target);if(o&&!out.Origin&&!out.origin)out.Origin=o;if(!out.Accept)out.Accept="*/*";return out}
function startsHls(text){return clean(text).trimStart().startsWith("#EXTM3U")}
function startsDash(text){return /<MPD[\s>]/i.test(clean(text).slice(0,4096))}
function bytesKind(bytes){if(!bytes||!bytes.length)return null;if(bytes.length>=12&&String.fromCharCode(bytes[4],bytes[5],bytes[6],bytes[7])==="ftyp")return"mp4";if(bytes.length>=4&&bytes[0]===26&&bytes[1]===69&&bytes[2]===223&&bytes[3]===163)return"mkv";if(bytes.length>=188&&bytes[0]===71&&(bytes.length<376||bytes[188]===71))return"mpegts";return null}
function decode(bytes){try{return new TextDecoder("utf-8").decode(bytes)}catch(_){var out="";for(var i=0;i<Math.min(bytes.length,262144);i++)out+=String.fromCharCode(bytes[i]);return out}}
async function resource(u,h){try{var r=await g.fetch(u,{headers:h,redirect:"follow",signal:timeout()});if(!r)return null;var type=r.headers&&r.headers.get?s(r.headers.get("content-type")):"",buffer=await r.arrayBuffer(),bytes=new Uint8Array(buffer),text=decode(bytes.slice(0,262144));return{ok:!!r.ok,status:r.status,url:s(r.url||u),type:type,bytes:bytes,text:text}}catch(_){return null}}
function proof(r){if(!r)return null;if(startsHls(r.text))return"hls";if(startsDash(r.text)||/application\/dash\+xml/i.test(r.type))return"dash";var binary=bytesKind(r.bytes);if(binary)return binary;if(/^video\//i.test(r.type)&&!/^video\/(?:svg|x-font)/i.test(r.type))return"video";return null}
function unescapeJs(v){try{return JSON.parse('"'+s(v).replace(/"/g,'\\"')+'"')}catch(_){return clean(v)}}
function unpack(source){var out=[],re=/eval\(function\(p,a,c,k,e,[rd]\)\{[\s\S]*?\}\(\s*['"]((?:\\.|[^'"\\])*)['"]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*['"]((?:\\.|[^'"\\])*)['"]\.split\(['"]\|['"]\)/g,m;while((m=re.exec(s(source)))!==null){try{var payload=unescapeJs(m[1]),radix=parseInt(m[2],10),count=parseInt(m[3],10),words=unescapeJs(m[4]).split("|");function key(n){return n.toString(radix)}for(var i=count-1;i>=0;i--){if(!words[i])continue;var rx=new RegExp("\\b"+key(i).replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+"\\b","g");payload=payload.replace(rx,words[i])}out.push(payload)}catch(_){}}return out}
function base64(source){var out=[],re=/(?:atob|base64_decode)\(\s*['"]([A-Za-z0-9+/=]{16,})['"]\s*\)/gi,m;while((m=re.exec(s(source)))!==null){try{var value=typeof g.atob==="function"?g.atob(m[1]):"";if(value)out.push(value)}catch(_){}}return out}
function candidates(text,base){var out=[],seen={};function add(v){var u=abs(v,base);if(!u||rejected(u)||seen[u])return;var low=u.toLowerCase();if(!/(?:\.m3u8|\.mp4|\.mkv|\.webm|\.mpd|\/hls\/|\/hls2\/|master\.m3u8|embed|player|watch|stream|video|\/e\/|\/v\/)/i.test(low))return;seen[u]=1;out.push(u)}function scan(body){body=clean(body);var patterns=[/(?:src|href|data-src|data-url|data-embed|data-player|data-link|data-file)=["']([^"']+)["']/gi,/(?:file|source|src|url|playlist|embedUrl|embed_url|contentUrl)\s*[:=]\s*["']([^"']+)["']/gi,/(https?:\/\/[^"'<>\s\\]+(?:m3u8|mp4|mkv|webm|mpd|embed|player|watch|stream|\/e\/|\/v\/)[^"'<>\s\\]*)/gi],m;for(var i=0;i<patterns.length;i++)while((m=patterns[i].exec(body))!==null)add(m[1])}scan(text);unpack(text).forEach(scan);base64(text).forEach(scan);return out.slice(0,c.maxCandidates)}
function normalizeRows(value){if(Array.isArray(value))return value;if(value&&typeof value==="object"){var keys=["streams","results","data"];for(var i=0;i<keys.length;i++)if(Array.isArray(value[keys[i]]))return value[keys[i]]}return[]}
function normalizeRow(row){if(!row||typeof row!=="object")return null;var u=s(row.url||row.streamUrl||row.stream||row.link||row.file);if(!u||rejected(u))return null;return Object.assign({},row,{url:u,headers:row.headers&&typeof row.headers==="object"?row.headers:{}})}
function compactRow(row,media){var subs=Array.isArray(row.subtitles)?row.subtitles.filter(function(x){return x&&x.url&&!rejected(x.url)}).slice(0,20):undefined;var out={name:s(row.name||c.providerName).slice(0,160),title:s(row.title||row.name||c.providerName).slice(0,240),url:media.url,quality:s(row.quality||"HD").slice(0,40),headers:media.headers||row.headers||{},isDirect:true,type:media.kind};if(row.language)out.language=s(row.language);if(row.size)out.size=s(row.size);if(subs&&subs.length)out.subtitles=subs;return out}
function unique(rows){var out=[],seen={};rows.forEach(function(row){if(!row||!row.url||seen[row.url])return;seen[row.url]=1;out.push(row)});return out}
async function resolve(u,baseHeaders,referer,depth,seen){if(depth>c.maxDepth||rejected(u))return[];seen=seen||{};if(seen[u])return[];seen[u]=1;var h=headers(baseHeaders,referer,u),r=await resource(u,h);if(!r)return[];var kind=proof(r);if(kind)return[{url:r.url||u,kind:kind,headers:h}];var type=s(r.type).toLowerCase();if(/text\/html|application\/xhtml|javascript|json|text\//i.test(type)||/[<>{}\[\]"']/.test(r.text)){var next=candidates(r.text,r.url||u),jobs=next.slice(0,c.maxCandidates).map(function(v){return resolve(v,h,r.url||u,depth+1,seen)}),groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}return[]}
async function invoke(old,self,args){var settings=g.SCRAPER_SETTINGS&&typeof g.SCRAPER_SETTINGS==="object"?g.SCRAPER_SETTINGS:{};var attempts=[function(){return old.call(self,args[0],args[1],args[2],args[3])},function(){return old.call(self,args[0],args[1],args[2],args[3],settings)},function(){return old.call(self,{tmdbId:args[0],mediaType:args[1],season:args[2],episode:args[3],settings:settings})}];for(var i=0;i<attempts.length;i++){try{var rows=normalizeRows(await attempts[i]());if(rows.length)return rows}catch(_){}}return[]}
async function tvRows(old,self,args){var native=await invoke(old,self,args),jobs=[];native.slice(0,c.maxCandidates).forEach(function(raw){var row=normalizeRow(raw);if(!row)return;var ref=s(row.headers&&(row.headers.Referer||row.headers.referer)||row.referer||row.url);jobs.push(resolve(row.url,row.headers,ref,0,{}).then(function(found){return found.map(function(media){return compactRow(row,media)})}))});var groups=await Promise.all(jobs),out=[];groups.forEach(function(group){out=out.concat(group)});return unique(out)}
function install(obj,key){if(!obj||typeof obj[key]!=="function"||obj[key].__nuvioTvDirectV2)return false;var old=obj[key],wrap=async function(tmdbId,mediaType,season,episode){return tvRows(old,this,arguments)};wrap.__nuvioTvDirectV2=true;obj[key]=wrap;return true}
var installed=false;try{if(typeof module!=="undefined"&&module.exports)installed=install(module.exports,"getStreams")}catch(_){}try{if(g&&typeof g.getStreams==="function"){if(installed&&typeof module!=="undefined"&&module.exports)g.getStreams=module.exports.getStreams;else install(g,"getStreams")}}catch(_){}
})(typeof globalThis!=="undefined"?globalThis:this,{"providerName":"DesiFlix","maxDepth":4,"maxCandidates":14,"timeoutMs":14000,"blockedHosts":[]});

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
