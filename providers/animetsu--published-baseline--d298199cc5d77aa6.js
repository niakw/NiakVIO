const _0x1b3810=_0x1ae2;(function(_0x436904,_0x9a348d){const _0x2d2060={_0x1faa75:0x1db,_0x5a4589:0x1be,_0x483280:0x1fc,_0x4b1f95:0x1e9,_0x526cf3:0x210,_0x2ee1fa:0x1ae},_0x1acc7f=_0x1ae2,_0x31731f=_0x436904();while(!![]){try{const _0x42f9df=parseInt(_0x1acc7f(_0x2d2060._0x1faa75))/0x1*(parseInt(_0x1acc7f(_0x2d2060._0x5a4589))/0x2)+parseInt(_0x1acc7f(_0x2d2060._0x483280))/0x3*(-parseInt(_0x1acc7f(_0x2d2060._0x4b1f95))/0x4)+parseInt(_0x1acc7f(0x1f2))/0x5*(parseInt(_0x1acc7f(0x1c3))/0x6)+parseInt(_0x1acc7f(0x1d9))/0x7*(parseInt(_0x1acc7f(0x1d5))/0x8)+parseInt(_0x1acc7f(0x1f5))/0x9*(parseInt(_0x1acc7f(0x1b9))/0xa)+parseInt(_0x1acc7f(0x1e2))/0xb*(-parseInt(_0x1acc7f(_0x2d2060._0x526cf3))/0xc)+-parseInt(_0x1acc7f(_0x2d2060._0x2ee1fa))/0xd*(parseInt(_0x1acc7f(0x1b6))/0xe);if(_0x42f9df===_0x9a348d)break;else _0x31731f['push'](_0x31731f['shift']());}catch(_0x54ecec){_0x31731f['push'](_0x31731f['shift']());}}}(_0x56cd,0xb25de));var __async=(_0x2ea7d8,_0x3c67f6,_0x542a7f)=>{return new Promise((_0x5c99ff,_0x163440)=>{const _0x6f7606={_0x44cd62:0x1bd},_0x583aee={_0x4977a0:0x1dd},_0x1ff76b=_0x1ae2;var _0x19a76d=_0x78eaf2=>{const _0x257f7b=_0x1ae2;try{_0x3698bc(_0x542a7f[_0x257f7b(_0x583aee._0x4977a0)](_0x78eaf2));}catch(_0x504a09){_0x163440(_0x504a09);}},_0x40c560=_0x1526d5=>{const _0x9249e=_0x1ae2;try{_0x3698bc(_0x542a7f[_0x9249e(_0x6f7606._0x44cd62)](_0x1526d5));}catch(_0x211bd8){_0x163440(_0x211bd8);}},_0x3698bc=_0x2a44c0=>_0x2a44c0['done']?_0x5c99ff(_0x2a44c0['value']):Promise[_0x1ff76b(0x215)](_0x2a44c0['value'])['then'](_0x19a76d,_0x40c560);_0x3698bc((_0x542a7f=_0x542a7f['apply'](_0x2ea7d8,_0x3c67f6))['next']());});},PROVIDER_NAME='Animetsu',TMDB_API_KEY='439c478a771f35c05022f9feabcca01c',BASE_URL='https://animetsu.live/v2/api',PROXY_URL=_0x1b3810(0x1d2),MOBILE_UAS=['Mozilla/5.0\x20(Linux;\x20Android\x2014;\x20Pixel\x208\x20Pro)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/124.0.0.0\x20Mobile\x20Safari/537.36',_0x1b3810(0x20f),'Mozilla/5.0\x20(Linux;\x20Android\x2012;\x20Pixel\x206)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/115.0.0.0\x20Mobile\x20Safari/537.36',_0x1b3810(0x1cb)];function getHeaders(_0x160481=null){const _0x5c25dd={_0x52692d:0x1f1},_0x41dcac=_0x1b3810,_0xed24f2=_0x160481||MOBILE_UAS[Math['floor'](Math[_0x41dcac(0x217)]()*MOBILE_UAS['length'])];return{'User-Agent':_0xed24f2,'Referer':_0x41dcac(_0x5c25dd._0x52692d),'Origin':_0x41dcac(0x1f1),'Accept-Language':_0x41dcac(0x1f8)};}var DOMAINS_JSON_URL=_0x1b3810(0x1e3),cachedDomains=null,domainCacheTime=0x0,DOMAIN_CACHE_TTL=0x4*0x3c*0x3c*0x3e8;function refreshDomains(){const _0x3fa51f={_0x2e3524:0x1c2};return __async(this,null,function*(){const _0x23c754=_0x1ae2,_0x19d3eb=Date['now']();if(cachedDomains&&_0x19d3eb-domainCacheTime<DOMAIN_CACHE_TTL)return cachedDomains;try{const _0x1908ea=yield fetch(DOMAINS_JSON_URL);if(_0x1908ea['ok']){const _0x48f10a=yield _0x1908ea[_0x23c754(0x1df)]();if(_0x48f10a){cachedDomains=_0x48f10a,domainCacheTime=_0x19d3eb;if(_0x48f10a['gojo_base'])BASE_URL=_0x48f10a['gojo_base']+_0x23c754(0x201);console['log']('['+PROVIDER_NAME+']\x20Domains\x20updated:\x20BASE_URL='+BASE_URL);}}}catch(_0x4b0a80){console['log']('['+PROVIDER_NAME+_0x23c754(_0x3fa51f._0x2e3524)+BASE_URL);}return cachedDomains||{};});}function manifest(){const _0x65c03d={_0x5e6e2e:0x1f3,_0x1e41ad:0x1bc},_0x454c2f=_0x1b3810;return{'id':'animetsu','name':_0x454c2f(0x1f7),'description':_0x454c2f(0x1b8),'version':'1.0.1','logo':'https://animetsu.live/favicon.ico','background':'https://animetsu.live/favicon.ico','types':['tv',_0x454c2f(_0x65c03d._0x5e6e2e),_0x454c2f(0x1cd)],'resources':['stream'],'idPrefixes':['tt',_0x454c2f(_0x65c03d._0x1e41ad)]};}function extractM3u8Qualities(_0x1cda90,_0x2e224b){const _0x4f5cdb={_0x4480c1:0x216,_0x380c2b:0x1f4,_0x30f4c0:0x202,_0x28187e:0x1d7,_0x53506f:0x1d8};return __async(this,null,function*(){const _0x50dd87=_0x1ae2;try{const _0x478bab=yield fetch(_0x1cda90,{'headers':_0x2e224b});if(!_0x478bab['ok'])return null;const _0x3ea20c=yield _0x478bab['text'](),_0x5cf4fb=_0x3ea20c[_0x50dd87(0x1e4)]('\x0a');let _0x2e1fa9=[],_0x4fc3a1=null;const _0x269fc6=_0x1cda90[_0x50dd87(_0x4f5cdb._0x4480c1)]('?'),_0x3c7c8f=_0x269fc6>-0x1?_0x1cda90['substring'](_0x269fc6):'',_0x4f11cc=_0x269fc6>-0x1?_0x1cda90[_0x50dd87(0x1e6)](0x0,_0x269fc6):_0x1cda90,_0x3d4849=_0x4f11cc[_0x50dd87(0x1e6)](0x0,_0x4f11cc[_0x50dd87(_0x4f5cdb._0x380c2b)]('/'));for(let _0x2a8ea6=0x0;_0x2a8ea6<_0x5cf4fb[_0x50dd87(0x207)];_0x2a8ea6++){let _0x7e314e=_0x5cf4fb[_0x2a8ea6]['trim']();if(_0x7e314e['startsWith']('#EXT-X-STREAM-INF')){const _0x63c484=_0x7e314e[_0x50dd87(_0x4f5cdb._0x30f4c0)](/RESOLUTION=\d+x(\d+)/);_0x4fc3a1=_0x63c484?_0x63c484[0x1]+'p':'Unknown';}else{if(_0x7e314e&&!_0x7e314e['startsWith']('#')&&_0x4fc3a1){let _0x4add9=_0x7e314e[_0x50dd87(0x213)]('http')?_0x7e314e:_0x3d4849+'/'+_0x7e314e;_0x3c7c8f&&!_0x4add9['includes']('?')&&(_0x4add9+=_0x3c7c8f),_0x2e1fa9[_0x50dd87(_0x4f5cdb._0x28187e)]({'quality':_0x4fc3a1,'url':_0x4add9}),_0x4fc3a1=null;}}}return _0x2e1fa9['length']>0x0?_0x2e1fa9:null;}catch(_0x40176f){return console['log']('['+PROVIDER_NAME+_0x50dd87(_0x4f5cdb._0x53506f)+_0x40176f['message']),null;}});}function search(_0xed2861,_0x3e6e91){return __async(this,null,function*(){return[];});}function makeStream(_0x3d2c51,_0x12805a,_0x67cc5d,_0x57b336,_0x2b500a,_0x193449,_0x1b2d8e,_0x1942b6){const _0x516b2f={_0x3510ac:0x211,_0xca2dcd:0x1c4,_0x143367:0x1bb,_0x4f560a:0x1de};return __async(this,null,function*(){const _0x56b543=_0x1ae2;let _0x3c01a7=_0x2b500a,_0x31ab21=!_0x2b500a[_0x56b543(_0x516b2f._0x3510ac)]('.mp4'),_0xdbe312=_0x57b336[_0x56b543(0x1dc)](),_0x2d67fb=getHeaders(_0x1942b6);const _0x1a7819={'name':''+_0x3d2c51+_0x67cc5d+'\x20('+_0xdbe312+')','title':''+_0x12805a+_0x67cc5d+'\x20('+_0xdbe312+')','size':''+_0x12805a+_0x67cc5d+'\x20('+_0xdbe312+')','url':_0x3c01a7,'quality':_0x193449,'behaviorHints':{'proxyHeaders':{'request':_0x2d67fb},'notWebReady':!![]}};if(_0x31ab21){_0x1a7819[_0x56b543(_0x516b2f._0xca2dcd)]=_0x2d67fb;const _0x201f2d=yield extractM3u8Qualities(_0x3c01a7,_0x2d67fb);if(_0x201f2d){const _0x2817c0=_0x201f2d['find'](_0x3a3fb1=>_0x3a3fb1['quality']==='1080p')||_0x201f2d[_0x56b543(_0x516b2f._0x143367)](_0x294ec9=>_0x294ec9[_0x56b543(0x1de)]==='720p')||_0x201f2d[0x0];_0x1a7819['url']=_0x2817c0['url']+'#ext=.m3u8',_0x1a7819['quality']=_0x2817c0['quality'],console['log']('['+PROVIDER_NAME+_0x56b543(0x1da)+_0x2817c0[_0x56b543(_0x516b2f._0x4f560a)]);}else _0x1a7819[_0x56b543(0x1c9)]=_0x3c01a7+'#ext=.m3u8';}return _0x1a7819;});}function _0x56cd(){const _0x5643b8=['zMXVB3i','C3vIC3rYAw5N','l2v4DgvYBMfSx2LKCZ9HCgLFA2v5pq','BMfTzq','odqZnJyWvwnys3Hf','yw5Pswq','xsbtzwfYy2HPBMCGvfzeqIbMB3iGC2vYAwvZoIa','C2vHC29UtNvTyMvY','xsboBYbYzxn1BhrZigzVDw5KigzVCIbXDwvYEs4','y292zxjFAw1Hz2u','Ahr0Chm6lY9HCgK0lNrOzxr2zgiUy29Tl3y0l3nLyxjJAd9XDwvYEt0','twvKAwe','Ahr0Chm6lY9HBMLTzxrZDs5SAxzLlW','nurqDMXwtq','Bw92Awu','BgfZDeLUzgv4t2y','mtaZndaYmJz5qwn5qwm','Dg9Rzw4','qw5PBwv0C3u','zw4TvvmSzw47Ct0WlJK','zgf0yq','xsbbDhrLBxb0Aw5NifrnreiGBwf0AcbMB3iGve1eqIbjrdOG','xsbtzwfYy2HPBMCGzM9YoIa','mtjZCg1suNC','yMfUBMvY','lMPZB24','zhvI','ieu9','l3yYl2fWAq','Bwf0y2G','ksb8ievWoIa','xsbtA2LWCgLUzYbUB24Tyw5PBwuGBwvKAweGkeDLBNjLCZOG','CMvWBgfJzq','xsbuturcienHBgn1Bgf0zwqGywjZB2X1DguGzxbPC29KztOG','BgvUz3rO','C291CMnLCW','yxbWBgLJyxrPB24VANnVBG','icHzzwfYoIa','C2XPy2u','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY90DI8','CMvSzwfZzv9KyxrL','z2vUCMvZ','tw96AwXSys81lJaGkeXPBNv4oYbbBMrYB2LKideZoYbtts1tote4qIKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeXnI4WlJaUmcbnB2jPBguGu2fMyxjPlZuZnY4ZnG','mZzZweDRALa','Aw5JBhvKzxm','CgfKu3rHCNq','C3rHCNrZv2L0Aa','zgLV','CMvZB2X2zq','Aw5KzxHpzG','CMfUzg9T','ifnLyxnVBIa','zxHLyW','BNvTyMvY','C3rYAw5NAwz5','mtnqC1vrALe','C2vHC29Ux251BwjLCG','qw5PBwf0Aw9U','xsbnyxrJAgvKihzPysbbBMLmAxn0ienVDMvYl0jHBM5LCIbjBwfNzsbjrce','DgvZDa','xsbbDhrLBxb0Aw5NifjLz2v4ie1HDgGGzM9YieLnrei6ia','zw5NBgLZAa','l2vWAxnVzgvZl2rLzMf1Bhq/C2vHC29Upq','mta5nZu5nZjvqwnyBg0','AM9PBG','qw5PBwuGC3rYzwfTCYbUyxrPDMvSEsbMB3iGtNv2Aw8GDMLHiefUAw1LDhn1iefqss4','mtb2yMXTBK0','DgL0Bgu','zMLUza','Dg1KyG','DgHYB3C','mtjmyNbbq2G','BwvZC2fNzq','B3jPz2LUywXFBgfUz3vHz2u','CM9TywPP','xsbeB21HAw4GCMvMCMvZAcbMywLSzwqSihvZAw5NigrLzMf1Bhq6ia','nJuWmJK5mNLOvuzjqW','AgvHzgvYCW','DhzKyL9Pza','qxv0BW','lcbmyw5NoIa','CMvZDwX0CW','DxjS','xsboBYbYzxn1BhrZihDPDgGGC2vHC29UigfWCgvUzgvKlIbuCNLPBMCGyMfZzsb0AxrSztOG','tw96AwXSys81lJaGkgLqAg9UztSGq1bvigLqAg9UzsbpuYaXn18WigXPA2uGtwfJie9tifGPiefWCgXLv2vIs2L0lZyWns4XlJe1icHlsfrntcWGBgLRzsbhzwnRBYKGvMvYC2LVBI8XnY4Wie1VyMLSzs8XnuuXndGGu2fMyxjPlZyWnc4X','C3vICW','yw5PBwu','w2eTEKeTwI9D','ywjZB2X1DgvoDw1Izxi','xsbbDhrLBxb0Aw5NifrwreiGtwf0AcbMB3iGvfzeqJOG','p3nLCNzLCJ0','Ahr0Chm6lY9ZD2LMDhn0CMvHBs50B3aVChjVEhK','BgfYz2u','Bg9N','mZyXmZzVyuTjt2W','C2vHC29UCW','ChvZAa','xsbgywLSzwqGDg8GCgfYC2uGttnvodOG','mty4mfDfAuP4qW','xsbgB3jJzwqGttnvocbrDwfSAxr5oIa','mJeWndn2u2rPvuG','Dg9vChbLCKnHC2u','BMv4Da','CxvHBgL0Eq','ANnVBG','zxbPC29Kzxm','wY0Uxq','mZK3nZCZmKzsugPfzW','Ahr0Chm6lY9YyxCUz2L0AhvIDxnLCMnVBNrLBNqUy29Tl1nHDxjHyMHlyxbLCNDHBI9vDgLSCY9YzwzZl2HLywrZl21HAw4VDxjSCY5QC29U','C3bSAxq'];_0x56cd=function(){return _0x5643b8;};return _0x56cd();}function _0x1ae2(_0x40948a,_0x4bc6aa){_0x40948a=_0x40948a-0x1ac;const _0x56cd0f=_0x56cd();let _0x1ae205=_0x56cd0f[_0x40948a];if(_0x1ae2['LKlPzr']===undefined){var _0x423c15=function(_0x5345af){const _0x264366='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x2ea7d8='',_0x3c67f6='';for(let _0x542a7f=0x0,_0x5c99ff,_0x163440,_0x19a76d=0x0;_0x163440=_0x5345af['charAt'](_0x19a76d++);~_0x163440&&(_0x5c99ff=_0x542a7f%0x4?_0x5c99ff*0x40+_0x163440:_0x163440,_0x542a7f++%0x4)?_0x2ea7d8+=String['fromCharCode'](0xff&_0x5c99ff>>(-0x2*_0x542a7f&0x6)):0x0){_0x163440=_0x264366['indexOf'](_0x163440);}for(let _0x40c560=0x0,_0x3698bc=_0x2ea7d8['length'];_0x40c560<_0x3698bc;_0x40c560++){_0x3c67f6+='%'+('00'+_0x2ea7d8['charCodeAt'](_0x40c560)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x3c67f6);};_0x1ae2['RnQdzg']=_0x423c15,_0x1ae2['SFBVVQ']={},_0x1ae2['LKlPzr']=!![];}const _0x5202c4=_0x56cd0f[0x0],_0x59a624=_0x40948a+_0x5202c4,_0x5eddea=_0x1ae2['SFBVVQ'][_0x59a624];return!_0x5eddea?(_0x1ae205=_0x1ae2['RnQdzg'](_0x1ae205),_0x1ae2['SFBVVQ'][_0x59a624]=_0x1ae205):_0x1ae205=_0x5eddea,_0x1ae205;}function fetchJson(_0x10c064,_0x838dd0){const _0x337eab={_0x42022c:0x1df};return __async(this,null,function*(){const _0x21f765=_0x1ae2;try{const _0x46fb12=new Promise((_0x2117c7,_0x4c7a04)=>{setTimeout(()=>_0x4c7a04(new Error('timeout')),0xfa0);}),_0x2f0598=yield Promise['race']([fetch(_0x10c064,_0x838dd0),_0x46fb12]);if(!_0x2f0598['ok'])return null;return yield _0x2f0598[_0x21f765(_0x337eab._0x42022c)]();}catch(_0x22f476){return null;}});}function aniListBridge(_0x38fe92){const _0x179df4={_0x56c07e:0x1f9};return __async(this,null,function*(){const _0x55b0f3=_0x1ae2,_0x32a05c='\x0a\x20\x20\x20\x20query\x20($search:\x20String)\x20{\x0a\x20\x20\x20\x20\x20\x20Media\x20(search:\x20$search,\x20type:\x20ANIME)\x20{\x0a\x20\x20\x20\x20\x20\x20\x20\x20id\x0a\x20\x20\x20\x20\x20\x20}\x0a\x20\x20\x20\x20}\x0a\x20\x20\x20\x20';try{const _0x3ab2de=yield fetch('https://graphql.anilist.co',{'method':'POST','headers':Object['assign'](getHeaders(),{'Content-Type':'application/json','Accept':'application/json'}),'body':JSON[_0x55b0f3(0x1ad)]({'query':_0x32a05c,'variables':{'search':_0x38fe92}})});if(!_0x3ab2de['ok'])return null;const _0x346a87=yield _0x3ab2de['json']();if(_0x346a87&&_0x346a87[_0x55b0f3(_0x179df4._0x56c07e)]&&_0x346a87['data'][_0x55b0f3(0x1f0)])return{'aniId':_0x346a87[_0x55b0f3(_0x179df4._0x56c07e)]['Media']['id']};}catch(_0x286b14){}return null;});}function getAbsoluteEpisode(_0x3db03b,_0x4185bd,_0x4bf4b4,_0x55ddd6,_0x4f6e6e){const _0x4db530={_0x5ed36a:0x1c5,_0x430071:0x1eb,_0x2cf5f7:0x1f9,_0x2dd162:0x1f6,_0x3b07af:0x1ef,_0x19da72:0x1f9,_0x52973a:0x1bb,_0x43a134:0x1d0,_0x58e106:0x1b5,_0x1f0efe:0x1e0,_0x5c977d:0x219,_0x455258:0x1d4,_0x416fea:0x1fa,_0x4c0cd4:0x1d6,_0x6cb9b5:0x1d6};return __async(this,null,function*(){const _0x3d20ff=_0x1ae2;if(_0x4185bd===_0x3d20ff(0x1f3))return 0x1;let _0x22bd86=_0x55ddd6,_0x46aca4=null,_0xf109eb=null;try{const _0x31a843=yield fetchJson(_0x3d20ff(0x20c)+_0x3db03b+_0x3d20ff(0x1e7)+TMDB_API_KEY);_0x31a843&&(_0x46aca4=_0x31a843['imdb_id'],_0xf109eb=_0x31a843[_0x3d20ff(_0x4db530._0x5ed36a)]);}catch(_0x220014){}if(!_0xf109eb&&_0x4f6e6e)try{console[_0x3d20ff(0x1d4)]('['+PROVIDER_NAME+_0x3d20ff(_0x4db530._0x430071)+_0x4f6e6e);const _0x47cb84='777140fb-de92-440a-aec2-95eb51e2d7ab',_0x35a4d6=yield fetchJson('https://api4.thetvdb.com/v4/login',{'method':'POST','headers':{'Content-Type':'application/json'},'body':JSON['stringify']({'apikey':_0x47cb84})});if(_0x35a4d6&&_0x35a4d6[_0x3d20ff(_0x4db530._0x2cf5f7)]&&_0x35a4d6[_0x3d20ff(_0x4db530._0x2cf5f7)][_0x3d20ff(_0x4db530._0x2dd162)]){const _0x5b605d=yield fetchJson(_0x3d20ff(_0x4db530._0x3b07af)+encodeURIComponent(_0x4f6e6e),{'headers':{'Authorization':'Bearer\x20'+_0x35a4d6[_0x3d20ff(_0x4db530._0x2cf5f7)][_0x3d20ff(_0x4db530._0x2dd162)]}});if(_0x5b605d&&_0x5b605d[_0x3d20ff(_0x4db530._0x19da72)]){const _0x38fad2=_0x5b605d[_0x3d20ff(0x1f9)][_0x3d20ff(_0x4db530._0x52973a)](_0x321abb=>_0x321abb['type']==='series');if(_0x38fad2){const _0x25e6c3=_0x38fad2['id']||_0x38fad2['tvdb_id'];_0x25e6c3&&(_0xf109eb=parseInt(String(_0x25e6c3)[_0x3d20ff(0x205)](/^series-/,''),0xa),console[_0x3d20ff(0x1d4)]('['+PROVIDER_NAME+']\x20Resolved\x20TVDB\x20ID\x20'+_0xf109eb+'\x20from\x20search'));}}}}catch(_0x38d891){}if(_0xf109eb)try{console[_0x3d20ff(0x1d4)]('['+PROVIDER_NAME+_0x3d20ff(_0x4db530._0x43a134)+_0xf109eb);const _0x34df74='777140fb-de92-440a-aec2-95eb51e2d7ab',_0x5a80ea=yield fetchJson('https://api4.thetvdb.com/v4/login',{'method':'POST','headers':{'Content-Type':_0x3d20ff(0x209)},'body':JSON[_0x3d20ff(0x1ad)]({'apikey':_0x34df74})});if(_0x5a80ea&&_0x5a80ea['data']&&_0x5a80ea['data'][_0x3d20ff(_0x4db530._0x2dd162)]){const _0xdc9aea=yield fetchJson('https://api4.thetvdb.com/v4/series/'+_0xf109eb+_0x3d20ff(_0x4db530._0x58e106)+_0x4bf4b4,{'headers':{'Authorization':'Bearer\x20'+_0x5a80ea['data'][_0x3d20ff(_0x4db530._0x2dd162)]}});if(_0xdc9aea&&_0xdc9aea['data']&&_0xdc9aea['data']['episodes']){const _0x1ec331=_0xdc9aea[_0x3d20ff(_0x4db530._0x19da72)][_0x3d20ff(_0x4db530._0x1f0efe)]['find'](_0x49617a=>_0x49617a[_0x3d20ff(0x1ec)]==_0x4bf4b4&&_0x49617a[_0x3d20ff(0x1ac)]==_0x55ddd6);if(_0x1ec331&&_0x1ec331['absoluteNumber'])return console['log']('['+PROVIDER_NAME+']\x20TVDB\x20Math\x20calculated\x20absolute\x20episode:\x20'+_0x1ec331['absoluteNumber']),_0x1ec331[_0x3d20ff(0x1cf)];}}}catch(_0x8cd329){}if(_0x46aca4)try{console['log']('['+PROVIDER_NAME+_0x3d20ff(0x1b3)+_0x46aca4);const _0x53d2f4='https://aiometadata.elfhosted.com/stremio/80d082c4-6e99-4c97-a67d-3d9e242685ce/meta/series/'+_0x46aca4+_0x3d20ff(0x1fe),_0x2ae4ca=yield fetch(_0x53d2f4);if(_0x2ae4ca&&_0x2ae4ca['ok']){const _0x5f5d40=yield _0x2ae4ca['text']();let _0x2c988a=0x0,_0x5ca0b2=![];const _0x10c8ed=/"season"\s*:\s*(\d+)/g;let _0xc5fb66;while((_0xc5fb66=_0x10c8ed[_0x3d20ff(_0x4db530._0x5c977d)](_0x5f5d40))!==null){_0x5ca0b2=!![];const _0x508313=parseInt(_0xc5fb66[0x1]);_0x508313>0x0&&_0x508313<_0x4bf4b4&&_0x2c988a++;}if(_0x5ca0b2){let _0x1765f5=_0x2c988a+_0x55ddd6;return console[_0x3d20ff(0x1d4)]('['+PROVIDER_NAME+']\x20Regex\x20Math\x20calculated\x20absolute\x20episode:\x20'+_0x1765f5),_0x1765f5;}}}catch(_0x223fbf){}try{console[_0x3d20ff(_0x4db530._0x455258)]('['+PROVIDER_NAME+_0x3d20ff(_0x4db530._0x416fea)+_0x3db03b);const _0x3337de='https://api.themoviedb.org/3/tv/'+_0x3db03b+'?api_key='+TMDB_API_KEY,_0x400b82=yield fetchJson(_0x3337de,{});if(_0x400b82&&_0x400b82[_0x3d20ff(_0x4db530._0x4c0cd4)]){let _0x241726=0x0;const _0x59d19e=_0x400b82[_0x3d20ff(_0x4db530._0x6cb9b5)]['filter'](_0x1628f5=>_0x1628f5[_0x3d20ff(0x1af)]>0x0&&_0x1628f5[_0x3d20ff(0x1af)]<_0x4bf4b4);for(let _0x18ffd7 of _0x59d19e){_0x241726+=_0x18ffd7['episode_count'];}return _0x241726+=_0x55ddd6,console['log']('['+PROVIDER_NAME+_0x3d20ff(0x206)+_0x241726),_0x241726;}}catch(_0xdc1694){}return _0x22bd86;});}function getStreams(_0x37704d,_0x218083,_0x459b3d,_0x7ca264){const _0x1f9d8e={_0x47a5f1:0x1e5,_0x325ac1:0x217,_0x3719b2:0x1c0,_0x248fe2:0x204,_0x522468:0x1c7,_0x2e76eb:0x20d,_0x4a5ef5:0x1e4,_0x33d9f2:0x1e4,_0x5e5666:0x218,_0x266a14:0x1fb,_0x4c8558:0x1d4,_0x9e01fe:0x1ce,_0x4c9901:0x1e1,_0x494d07:0x1ba,_0x98eb5f:0x1b1,_0x494064:0x207,_0x45ea73:0x1ba,_0x150bd8:0x1ba,_0x10d000:0x203,_0x35e7c4:0x214,_0x330968:0x1d1,_0x1f94dd:0x208,_0x410514:0x20b,_0x1897a5:0x212,_0x4a112a:0x1de,_0x5832f8:0x1c6,_0x1f72e7:0x1cc,_0x2c9f40:0x1d7,_0x4a0c64:0x1bf};return __async(this,null,function*(){const _0x5d7a26=_0x1ae2,_0x4ddd9d=MOBILE_UAS[Math[_0x5d7a26(_0x1f9d8e._0x47a5f1)](Math[_0x5d7a26(_0x1f9d8e._0x325ac1)]()*MOBILE_UAS[_0x5d7a26(0x207)])],_0x2ba8fd=getHeaders(_0x4ddd9d);console['log']('['+PROVIDER_NAME+']\x20Request:\x20ID='+_0x37704d+'\x20Type='+_0x218083+'\x20S='+_0x459b3d+_0x5d7a26(0x200)+_0x7ca264),yield refreshDomains();let _0x573ff5=[];try{const _0x104193=_0x218083==='tv'||_0x218083==='series'||_0x218083==='anime',_0x207569=_0x104193?'tv':'movie',_0x14625b=yield fetchJson('https://api.themoviedb.org/3/'+_0x207569+'/'+_0x37704d+'?api_key='+TMDB_API_KEY);if(!_0x14625b)return _0x573ff5;const _0x382f2a=_0x14625b['genres']&&_0x14625b['genres']['some'](_0x55dd04=>_0x55dd04[_0x5d7a26(0x1e8)]===_0x5d7a26(0x1b0)),_0x40d9b6=['ja','zh','ko'][_0x5d7a26(0x211)](_0x14625b[_0x5d7a26(_0x1f9d8e._0x3719b2)]);if(!_0x382f2a||!_0x40d9b6)return console['log']('['+PROVIDER_NAME+_0x5d7a26(_0x1f9d8e._0x248fe2)+(_0x14625b['genres']?_0x14625b[_0x5d7a26(0x20e)]['map'](_0x2f9226=>_0x2f9226[_0x5d7a26(0x1e8)])[_0x5d7a26(0x1b7)](',\x20'):'none')+_0x5d7a26(_0x1f9d8e._0x522468)+_0x14625b['original_language']+').'),_0x573ff5;let _0x1fd32f=_0x14625b['name']||_0x14625b['title'];if(!_0x1fd32f)return _0x573ff5;let _0x26c93f='';if(_0x14625b['release_date'])_0x26c93f=_0x14625b[_0x5d7a26(_0x1f9d8e._0x2e76eb)][_0x5d7a26(_0x1f9d8e._0x4a5ef5)]('-')[0x0];else{if(_0x14625b['first_air_date'])_0x26c93f=_0x14625b['first_air_date'][_0x5d7a26(0x1e4)]('-')[0x0];}let _0x346f8f=_0x1fd32f[_0x5d7a26(_0x1f9d8e._0x33d9f2)](':')[0x0]['trim'](),_0x1429a0=_0x346f8f;_0x104193&&_0x459b3d>0x1&&(_0x1429a0+=_0x5d7a26(_0x1f9d8e._0x5e5666)+_0x459b3d);console['log']('['+PROVIDER_NAME+_0x5d7a26(_0x1f9d8e._0x266a14)+_0x1429a0+_0x5d7a26(0x20a)+(_0x26c93f||'Unknown')+')');let _0xd096f9=yield fetchJson(BASE_URL+'/anime/search/?query='+encodeURIComponent(_0x1429a0),{'headers':_0x2ba8fd}),_0x40fe01=![];if(!_0xd096f9||!_0xd096f9['results']||_0xd096f9[_0x5d7a26(0x1c8)][_0x5d7a26(0x207)]===0x0){_0x1429a0!==_0x346f8f&&(console['log']('['+PROVIDER_NAME+_0x5d7a26(0x1ca)+_0x346f8f),_0xd096f9=yield fetchJson(BASE_URL+'/anime/search/?query='+encodeURIComponent(_0x346f8f),{'headers':_0x2ba8fd}),_0x40fe01=!![]);if(!_0xd096f9||!_0xd096f9['results']||_0xd096f9[_0x5d7a26(0x1c8)]['length']===0x0)return console['log']('['+PROVIDER_NAME+_0x5d7a26(0x1ed)),_0x573ff5;}let _0x369347=null,_0x477f15='',_0x28422e=_0x7ca264,_0x574c5=null,_0x4fe5cc=![];if(_0x104193){let _0x2dc1da=yield aniListBridge(_0x1429a0);if(_0x2dc1da&&_0x2dc1da['aniId'])_0x574c5=_0x2dc1da['aniId'],_0x4fe5cc=![];else _0x1429a0!==_0x346f8f&&(_0x2dc1da=yield aniListBridge(_0x346f8f),_0x2dc1da&&_0x2dc1da[_0x5d7a26(0x1ea)]&&(_0x574c5=_0x2dc1da['aniId'],_0x4fe5cc=!![]));}if(_0x574c5){console[_0x5d7a26(_0x1f9d8e._0x4c8558)]('['+PROVIDER_NAME+']\x20AniList\x20Mapping\x20found:\x20AniId='+_0x574c5);const _0x3ebd33=new RegExp(_0x5d7a26(_0x1f9d8e._0x9e01fe)+_0x574c5+_0x5d7a26(_0x1f9d8e._0x4c9901));for(let _0x2b980a of _0xd096f9['results']){const _0x252850=_0x2b980a[_0x5d7a26(0x1ee)]&&_0x2b980a[_0x5d7a26(0x1ee)][_0x5d7a26(0x1d3)]?_0x2b980a['cover_image']['large']:'',_0x5e1b02=_0x2b980a[_0x5d7a26(0x1fd)]||'';if(_0x3ebd33[_0x5d7a26(0x1b2)](_0x252850)||_0x3ebd33[_0x5d7a26(0x1b2)](_0x5e1b02)){_0x369347=_0x2b980a['id'],_0x477f15=_0x2b980a[_0x5d7a26(_0x1f9d8e._0x494d07)]['english']||_0x2b980a[_0x5d7a26(_0x1f9d8e._0x494d07)]['romaji'];_0x4fe5cc&&_0x104193&&_0x459b3d>0x1?_0x28422e=yield getAbsoluteEpisode(_0x37704d,_0x218083,_0x459b3d,_0x7ca264,_0x1fd32f):_0x28422e=_0x7ca264;console[_0x5d7a26(0x1d4)]('['+PROVIDER_NAME+_0x5d7a26(_0x1f9d8e._0x98eb5f));break;}}}if(!_0x369347){for(let _0x3bc7ba=0x0;_0x3bc7ba<_0xd096f9[_0x5d7a26(0x1c8)][_0x5d7a26(_0x1f9d8e._0x494064)];_0x3bc7ba++){let _0x1c8b33=_0xd096f9['results'][_0x3bc7ba];if(_0x26c93f&&_0x1c8b33['year']===parseInt(_0x26c93f)){_0x369347=_0x1c8b33['id'],_0x477f15=_0x1c8b33[_0x5d7a26(_0x1f9d8e._0x494d07)]['english']||_0x1c8b33[_0x5d7a26(_0x1f9d8e._0x45ea73)]['romaji'];break;}}!_0x369347&&(_0x369347=_0xd096f9['results'][0x0]['id'],_0x477f15=_0xd096f9[_0x5d7a26(0x1c8)][0x0][_0x5d7a26(_0x1f9d8e._0x150bd8)][_0x5d7a26(0x1b4)]||_0xd096f9[_0x5d7a26(0x1c8)][0x0][_0x5d7a26(0x1ba)][_0x5d7a26(0x1c1)]),_0x104193&&_0x459b3d>0x1&&_0x40fe01&&(_0x28422e=yield getAbsoluteEpisode(_0x37704d,_0x218083,_0x459b3d,_0x7ca264,_0x1fd32f));}console['log']('['+PROVIDER_NAME+']\x20Matched\x20ID:\x20'+_0x369347+'\x20('+_0x477f15+_0x5d7a26(_0x1f9d8e._0x10d000)+_0x28422e);const _0x3167fa=['kite',_0x5d7a26(_0x1f9d8e._0x35e7c4)],_0x114519=['sub',_0x5d7a26(0x1ff)];for(const _0x273689 of _0x3167fa){for(const _0x399b34 of _0x114519){const _0x180b87=BASE_URL+'/anime/oppai/'+_0x369347+'/'+_0x28422e+_0x5d7a26(_0x1f9d8e._0x330968)+_0x273689+'&source_type='+_0x399b34;try{const _0xc5dcb3=yield fetchJson(_0x180b87,{'headers':_0x2ba8fd});if(_0xc5dcb3&&_0xc5dcb3[_0x5d7a26(0x208)]&&_0xc5dcb3[_0x5d7a26(_0x1f9d8e._0x1f94dd)]['length']>0x0)for(let _0x518154 of _0xc5dcb3['sources']){if(_0x518154['url']){const _0x43e8a1=PROXY_URL+_0x518154[_0x5d7a26(0x1c9)],_0x473cf5=yield makeStream(PROVIDER_NAME,_0x273689['charAt'](0x0)['toUpperCase']()+_0x273689[_0x5d7a26(_0x1f9d8e._0x410514)](0x1),_0x104193?'\x20S'+String(_0x459b3d)[_0x5d7a26(_0x1f9d8e._0x1897a5)](0x2,'0')+'E'+String(_0x7ca264)['padStart'](0x2,'0'):'',_0x399b34,_0x43e8a1,_0x518154[_0x5d7a26(_0x1f9d8e._0x4a112a)]||_0x5d7a26(_0x1f9d8e._0x5832f8),_0xc5dcb3[_0x5d7a26(_0x1f9d8e._0x1f72e7)],_0x4ddd9d);if(_0x473cf5)_0x573ff5[_0x5d7a26(_0x1f9d8e._0x2c9f40)](_0x473cf5);}}}catch(_0x975fc4){console['log']('['+PROVIDER_NAME+']\x20Error\x20fetching\x20'+_0x273689+'\x20'+_0x399b34+':\x20'+_0x975fc4[_0x5d7a26(_0x1f9d8e._0x4a0c64)]);}}}}catch(_0x3de368){console[_0x5d7a26(0x1d4)]('['+PROVIDER_NAME+']\x20Error:\x20'+_0x3de368['message']);}return _0x573ff5;});}module['exports']={'manifest':manifest,'search':search,'getStreams':getStreams};

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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:9b4669ea3d4a */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"animetsu","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
