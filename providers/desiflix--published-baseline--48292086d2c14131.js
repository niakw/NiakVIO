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

/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:a7e43845497d */
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
  if(!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",DEFAULT_UA);
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
})(typeof globalThis!=="undefined"?globalThis:this,{"maxRows":6,"maxDepth":2,"maxCandidates":10,"timeoutMs":6500,"preserveOriginal":true,"implementationRevision":"playback-context-v3"});
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:f6d7a009c139 */
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
    if(!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=DEFAULT_UA;
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
    if(!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=DEFAULT_UA;has=true}
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"desiflix","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"platform-playback-context-v3"});
