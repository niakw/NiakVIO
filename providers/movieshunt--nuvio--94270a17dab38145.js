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
})(typeof globalThis!=="undefined"?globalThis:this,[["bW92aWVzaHVudC53b3Jr","movieshunt.casa"]]);
var _0x310f1c=_0x2f28;(function(_0x37811,_0x15a88d){var _0x56f970={_0x3d81d5:0x149,_0x31b5eb:0x184,_0x5ac781:0x133,_0x391c08:0x15b},_0x180768=_0x2f28,_0x41c7e9=_0x37811();while(!![]){try{var _0x38d53a=-parseInt(_0x180768(0x16a))/0x1*(parseInt(_0x180768(0x125))/0x2)+parseInt(_0x180768(0x17e))/0x3+-parseInt(_0x180768(_0x56f970._0x3d81d5))/0x4*(parseInt(_0x180768(_0x56f970._0x31b5eb))/0x5)+parseInt(_0x180768(0x17b))/0x6*(parseInt(_0x180768(0x13d))/0x7)+parseInt(_0x180768(0x18b))/0x8+-parseInt(_0x180768(_0x56f970._0x5ac781))/0x9+-parseInt(_0x180768(_0x56f970._0x391c08))/0xa*(-parseInt(_0x180768(0x12b))/0xb);if(_0x38d53a===_0x15a88d)break;else _0x41c7e9['push'](_0x41c7e9['shift']());}catch(_0x550585){_0x41c7e9['push'](_0x41c7e9['shift']());}}}(_0x16be,0xb1d13));var __async=(_0x1750ab,_0x374b0d,_0x425222)=>{var _0x1c7652={_0x2d9341:0x164};return new Promise((_0x25582f,_0x5b90ea)=>{var _0x21ba9b=_0x2f28,_0x55645f=_0x43b88e=>{var _0x1e680f=_0x2f28;try{_0x5dc19c(_0x425222[_0x1e680f(0x181)](_0x43b88e));}catch(_0x54a602){_0x5b90ea(_0x54a602);}},_0x17ebe3=_0x5d81cc=>{try{_0x5dc19c(_0x425222['throw'](_0x5d81cc));}catch(_0x4aa80f){_0x5b90ea(_0x4aa80f);}},_0x5dc19c=_0x12d3a0=>_0x12d3a0[_0x21ba9b(0x127)]?_0x25582f(_0x12d3a0[_0x21ba9b(0x161)]):Promise[_0x21ba9b(0x147)](_0x12d3a0[_0x21ba9b(0x161)])['then'](_0x55645f,_0x17ebe3);_0x5dc19c((_0x425222=_0x425222[_0x21ba9b(_0x1c7652._0x2d9341)](_0x1750ab,_0x374b0d))['next']());});},PROVIDER_NAME='MoviesHunt',TMDB_API_KEY='439c478a771f35c05022f9feabcca01c',movieshuntBase=_0x310f1c(0x16f),abhilinksBase='https://abhilinks.site',currentUA='Mozilla/5.0\x20(Linux;\x20Android\x2014;\x20Pixel\x208\x20Pro)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/124.0.0.0\x20Mobile\x20Safari/537.36',UAS=['Mozilla/5.0\x20(Linux;\x20Android\x2014;\x20Pixel\x208\x20Pro)\x20AppleWebKit/537.36\x20(KHTML,\x20like\x20Gecko)\x20Chrome/124.0.0.0\x20Mobile\x20Safari/537.36',_0x310f1c(0x146),_0x310f1c(0x154),_0x310f1c(0x12f)];function log(_0x31693e){console['log']('['+PROVIDER_NAME+']\x20'+_0x31693e);}function hdrs(_0x17e151){var _0x12b221=_0x310f1c;return Object['assign']({},{'User-Agent':currentUA,'Accept-Language':_0x12b221(0x150),'Accept':_0x12b221(0x171)},_0x17e151||{});}var FETCH_TIMEOUT=0x4e20;function raceTimeout(_0x59861b){return new Promise(function(_0x2d2fb3,_0x8108d5){setTimeout(function(){_0x8108d5(new Error('Timeout'));},_0x59861b);});}function fetchText(_0x5a461e,_0x39ad72){return __async(this,null,function*(){try{var _0x480aa8=yield Promise['race']([fetch(_0x5a461e,_0x39ad72||{}),raceTimeout(FETCH_TIMEOUT)]);if(_0x480aa8&&_0x480aa8['ok'])return yield _0x480aa8['text']();}catch(_0x206690){}return null;});}function _0x16be(){var _0x34b08e=['8j+tPsbxruiTreW','Ahr0Ca','8j+nVYa','tw96AwXSys81lJaGkgLqAg9UztSGq1bvigLqAg9UzsbpuYaXn18WigXPA2uGtwfJie9tifGPiefWCgXLv2vIs2L0lZyWns4XlJe1icHlsfrntcWGBgLRzsbhzwnRBYKGvMvYC2LVBI8XnY4Wie1VyMLSzs8XnuuXndGGu2fMyxjPlZyWnc4X','BMfTzq','iokaOIa','rLnm','mte1nJu0odzPuK9cAxK','ihjLC3vSDhm','zw4TvvmSzw47Ct0WlJu','ns4X','CMvWBgfJzq','DMnSB3vK','AhvIy2XVDwq','C3vIC3rYAw5N','zxHLyW','zMLYC3rFywLYx2rHDgu','nZuXnZuXte5xuMfp','D2vIlxjPCa','Aw5Uzxi','vhj5Aw5NihbVC3q6ia','DxjS','jMXHBMD1ywDLpwvUlvvt','8j+mIca','mJe2ma','zMXVB3i','tw96AwXSys81lJaGkeXPBNv4oYbbBMrYB2LKideZoYbtts1tote4qIKGqxbWBgvxzwjlAxqVntm3lJm2icHlsfrntcWGBgLRzsbhzwnRBYKGq2HYB21LlZeXnI4WlJaUmcbnB2jPBguGu2fMyxjPlZuZnY4ZnG','CMvZB2X2zq','ihWGuW','nZiWodHUB0rbsuG','Dg9mB3DLCKnHC2u','CxvHBgL0Eq','8j+uIca','ywXS','DgL0Bgu','ChvZAa','zw4TvvmSzw47Ct0WlJK','Cg9W','BwfYyxrOAq','yxrTB3m','tw96AwXSys81lJaGkeXPBNv4oYbbBMrYB2LKideYoYbqAxHLBca2ksbbChbSzvDLyKTPDc81mZCUmZyGkeTive1mlcbSAwTLieDLy2TVksbdAhjVBwuVmte1lJaUmc4Wie1VyMLSzsbtywzHCMKVntm3lJm2','CMfUzg9T','yMvUz2fSAq','lZ9Zpq','AgrY','tM8GDgL0BguGzNjVBsbuturc','CMfJzq','mtb0zK5lEuu','ihWG8j+uIIbbDg1VCW','C2vYAwvZ','ndGWCa','DgvSDwD1','vhj1zuHe','DMfSDwu','8j+oPsb4mJy0','ihn0CMvHBxmGzNjVBsa','yxbWBhK','zxHWB3j0CW','Edi2nq','reqGns4X','tuTw','qwjOAwXPBMTZigzLDgnOigzHAwXLza','mteWodG1B3jjDgzl','CMf3vgv4Da','C29YDa','mta4mha','rLnmDJi','Ahr0Chm6lY9TB3zPzxnODw50lNj1BG','Awr4','Dgv4Dc9ODg1SlgfWCgXPy2f0Aw9Ul3HODg1Sk3HTBcXHChbSAwnHDgLVBI94BwW7Ct0WlJKSkI8Qo3e9mc44','ihWG8j+oPYa','DhLWzq','DgvZDa','A2v5CW','BgvUz3rO','Aw5KzxG','EgXHpxm0Da','DhjPBq','CMvSzwfZzv9KyxrL','ndjMuMTVq1u','BwLU','Bwf0y2G','mZC4odq5mffXsuzICG','Dg9vChbLCKnHC2u','tM8GAhvIy2XVDwqVDMnSB3vKihrHC2TZ','BMv4Da','zgrWns4X','u2vHCMnOigzHAwXLza','nZvxtfDQDwm','Bwf4','8j+oPsb4mJy1','txvSDgKTqxvKAw8','8j+mKcbxruiTuKLq','mtbIAxq','D2vICMLW','nduWodaWmen4s0zkyW','ihWG','C3bSAxq','twf0y2HLCZOG','zMLSDgvY','tw96AwXSys81lJaGkfGXmtSGvwj1BNr1oYbmAw51Ecb4odzFnJq7ihj2oJe1mI4WksbhzwnRBY8YmdeWmdeWmsbgAxjLzM94lZe1mI4W','v29YA2vY','BgLUA3m','8j+uLYa','vgL0Bgu6ia','qufd','zhvHBa','Dw5KzwzPBMvK','BwfSyxLHBgfT','AgrYmta','Aw5KzxHpzG','AgrYmtaR','mtHtA1LguuG','AM9PBG','zg9Uzq','icbMzxrJAcbMywLSzwq','tM8GC3rYzwfTCYbMCM9TihrOAxmGCg9ZDcWGDhj5Aw5Nig5LEhqGBwf0y2G','CgfKu3rHCNq','nZCZoty3n2PuCeHSEq'];_0x16be=function(){return _0x34b08e;};return _0x16be();}function fetchJson(_0x1cdeba,_0x3e56f2){var _0x23b4e5={_0xc8e14b:0x15a};return __async(this,null,function*(){var _0x229ae8=_0x2f28;try{var _0x142245=yield Promise[_0x229ae8(_0x23b4e5._0xc8e14b)]([fetch(_0x1cdeba,_0x3e56f2||{}),raceTimeout(FETCH_TIMEOUT)]);if(_0x142245&&_0x142245['ok'])return yield _0x142245['json']();}catch(_0x181162){}return null;});}function getTMDBInfo(_0x30733c,_0xeacd58){return __async(this,null,function*(){var _0x3caf36=_0x2f28,_0x5dda87=_0xeacd58==='tv'||_0xeacd58===_0x3caf36(0x15d)?'tv':'movie',_0x2b1e06='https://api.themoviedb.org/3/'+_0x5dda87+'/'+_0x30733c+'?api_key='+TMDB_API_KEY+_0x3caf36(0x142);return yield fetchJson(_0x2b1e06,{'headers':{'User-Agent':currentUA}});});}function parseSearchResults(_0x4c2672){var _0x89d025={_0x460e94:0x13b,_0x343e96:0x12d,_0x3189fd:0x14f},_0x1c9dc8=_0x310f1c,_0x1c3113=[],_0x48ac38=/<h\d[^>]*class="[^"]*entry-title[^"]*"[^>]*>([\s\S]*?)<\/h\d>/gi,_0x3ee030;while((_0x3ee030=_0x48ac38[_0x1c9dc8(_0x89d025._0x460e94)](_0x4c2672))!==null){var _0x34d893=_0x3ee030[0x1],_0x4f8e1f=_0x34d893[_0x1c9dc8(0x17d)](/<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);if(_0x4f8e1f){var _0x154561=_0x4f8e1f[0x1];if(_0x154561[_0x1c9dc8(0x123)](_0x1c9dc8(_0x89d025._0x343e96))!==0x0)_0x154561=movieshuntBase+(_0x154561['startsWith']('/')?'':'/')+_0x154561;var _0x3f983b=_0x4f8e1f[0x2][_0x1c9dc8(0x137)](/<[^>]+>/g,'')[_0x1c9dc8(0x179)]();if(_0x3f983b[_0x1c9dc8(0x176)]>0x5)_0x1c3113[_0x1c9dc8(_0x89d025._0x3189fd)]({'title':_0x3f983b,'url':_0x154561});}}return _0x1c3113;}function searchSite(_0x42cbdf){var _0x3701e2={_0x1e445e:0x137,_0x2f384a:0x137,_0x226de9:0x179,_0x37fd30:0x14f,_0x5a8390:0x18f,_0x5017a0:0x17c,_0x1f1e86:0x176,_0x3d06db:0x126,_0x968c52:0x176,_0x21ae64:0x174,_0xad123a:0x123,_0x190f3a:0x176,_0x57d8fb:0x157,_0x11c285:0x176,_0x1b3ef4:0x134};return __async(this,null,function*(){var _0x2af5f9=_0x2f28,_0x2749b3=[],_0x191469=[_0x42cbdf['replace'](/'/g,'')['trim']()],_0xc65b00=_0x42cbdf[_0x2af5f9(_0x3701e2._0x1e445e)](/[^a-zA-Z0-9 ]/g,'\x20')[_0x2af5f9(_0x3701e2._0x2f384a)](/\s+/g,'\x20')[_0x2af5f9(_0x3701e2._0x226de9)]();if(_0xc65b00!==_0x191469[0x0])_0x191469['push'](_0xc65b00);var _0x2fe763=_0xc65b00['replace'](/\s*\d{4}\s*/g,'\x20')[_0x2af5f9(0x179)]();if(_0x2fe763&&_0x191469['indexOf'](_0x2fe763)<0x0)_0x191469[_0x2af5f9(_0x3701e2._0x37fd30)](_0x2fe763);var _0x5ead67=_0xc65b00[_0x2af5f9(0x18d)]('\x20')[_0x2af5f9(_0x3701e2._0x5a8390)](function(_0x22fdce){return _0x22fdce['length']>0x2;});while(_0x5ead67[_0x2af5f9(0x176)]>0x1){_0x5ead67[_0x2af5f9(0x151)]();var _0x56463=_0x5ead67['join']('\x20');if(_0x56463[_0x2af5f9(0x176)]>0x3&&_0x191469[_0x2af5f9(0x123)](_0x56463)<0x0)_0x191469[_0x2af5f9(0x14f)](_0x56463);}if(_0xc65b00){var _0x5a1b3a=_0xc65b00['split']('\x20');if(_0x5a1b3a['length']>0x1){var _0x368ef2=_0x5a1b3a['slice'](-Math[_0x2af5f9(_0x3701e2._0x5017a0)](0x2,_0x5a1b3a[_0x2af5f9(_0x3701e2._0x1f1e86)]))[_0x2af5f9(_0x3701e2._0x3d06db)]('\x20');if(_0x368ef2[_0x2af5f9(0x176)]>0x3&&_0x191469['indexOf'](_0x368ef2)<0x0)_0x191469['push'](_0x368ef2);var _0x35e876=_0x5a1b3a[_0x5a1b3a['length']-0x1];if(_0x35e876[_0x2af5f9(_0x3701e2._0x968c52)]>0x3&&/[a-zA-Z]/[_0x2af5f9(_0x3701e2._0x21ae64)](_0x35e876)&&_0x191469[_0x2af5f9(_0x3701e2._0xad123a)](_0x35e876)<0x0)_0x191469['push'](_0x35e876);}}for(var _0x5bef5a=0x0;_0x5bef5a<_0x191469[_0x2af5f9(_0x3701e2._0x190f3a)];_0x5bef5a++){var _0x1c3578=_0x191469[_0x5bef5a];if(_0x1c3578[_0x2af5f9(_0x3701e2._0x1f1e86)]<0x3)continue;var _0x12a8f2=movieshuntBase+_0x2af5f9(_0x3701e2._0x57d8fb)+encodeURIComponent(_0x1c3578),_0x4b7b7d=yield fetchText(_0x12a8f2,{'headers':hdrs()});if(!_0x4b7b7d)continue;var _0x218ded=parseSearchResults(_0x4b7b7d);if(_0x218ded&&_0x218ded[_0x2af5f9(0x176)])return log('Search\x20\x27'+_0x1c3578+'\x27\x20found\x20'+_0x218ded[_0x2af5f9(_0x3701e2._0x11c285)]+_0x2af5f9(_0x3701e2._0x1b3ef4)),_0x218ded;}return _0x2749b3;});}function matchHits(_0xbcc84a,_0x20027d,_0x5b86f5){var _0x30d2e5={_0x20b15a:0x14e,_0x5a85f2:0x14a,_0x3a0a88:0x137,_0x1b1b39:0x18d,_0x4dba11:0x176,_0x27dbfd:0x137,_0x40a905:0x123,_0x127221:0x179,_0x3aa121:0x18f,_0x3de717:0x16c},_0x5150b6={_0x22141d:0x176},_0x41eacf=_0x310f1c,_0x8b4d86=(_0x5b86f5?_0x20027d['name']:_0x20027d[_0x41eacf(_0x30d2e5._0x20b15a)])||'',_0x574091=_0x5b86f5?(_0x20027d['first_air_date']||'')['split']('-')[0x0]:(_0x20027d['release_date']||'')['split']('-')[0x0],_0x56e944=_0x8b4d86[_0x41eacf(_0x30d2e5._0x5a85f2)]()['replace'](/[\u2018\u2019\u201A\u201B\u2032\u2035]/g,'\x27'),_0x23e902=/\b(and|&|the|a|an)\b/g,_0x104c83=_0x56e944['replace'](_0x23e902,'')[_0x41eacf(_0x30d2e5._0x3a0a88)](/\s+/g,'\x20')['trim'](),_0x1a0806=_0x56e944[_0x41eacf(_0x30d2e5._0x1b1b39)](/\s+/)['filter'](function(_0x43c4f5){var _0x1a1bf9=_0x41eacf;return _0x43c4f5[_0x1a1bf9(_0x5150b6._0x22141d)]>0x1;}),_0x2950bc=[],_0x1695f2={};for(var _0x1bbcce=0x0;_0x1bbcce<_0xbcc84a[_0x41eacf(_0x30d2e5._0x4dba11)];_0x1bbcce++){var _0x3ea9ab=_0xbcc84a[_0x1bbcce],_0xea8102=_0x3ea9ab['title']||'',_0x44595a=_0x3ea9ab['url']||'';if(_0x1695f2[_0x44595a])continue;_0x1695f2[_0x44595a]=!![];var _0x135b70=_0xea8102[_0x41eacf(0x14a)]()['replace'](/[\u2018\u2019\u201A\u201B\u2032\u2035]/g,'\x27'),_0x45d4bd=0x0;if(_0x135b70===_0x56e944)_0x45d4bd+=0x64;else{if(_0x135b70['indexOf'](_0x56e944)>=0x0||_0x56e944['indexOf'](_0x135b70)>=0x0)_0x45d4bd+=0x32;else{var _0x311c89=_0x135b70[_0x41eacf(0x137)](_0x23e902,'')[_0x41eacf(_0x30d2e5._0x27dbfd)](/\s+/g,'\x20')[_0x41eacf(0x179)]();if(_0x311c89['indexOf'](_0x104c83)>=0x0||_0x104c83[_0x41eacf(_0x30d2e5._0x40a905)](_0x311c89)>=0x0)_0x45d4bd+=0x32;else{if(_0x311c89[_0x41eacf(_0x30d2e5._0x3a0a88)](/[^a-z0-9\s]/g,'')[_0x41eacf(0x179)]()===_0x104c83['replace'](/[^a-z0-9\s]/g,'')[_0x41eacf(_0x30d2e5._0x127221)]())_0x45d4bd+=0x3c;}}}if(_0x45d4bd===0x0&&_0x1a0806['length']>0x1){var _0x1e9e79=_0x135b70['split'](/\s+/)[_0x41eacf(_0x30d2e5._0x3aa121)](function(_0x5925f1){var _0x276692=_0x41eacf;return _0x5925f1[_0x276692(0x176)]>0x1;}),_0x46d0a0=0x0;for(var _0x1d6f28=0x0;_0x1d6f28<_0x1a0806['length'];_0x1d6f28++){for(var _0x3bca6c=0x0;_0x3bca6c<_0x1e9e79['length'];_0x3bca6c++){if(_0x1a0806[_0x1d6f28]===_0x1e9e79[_0x3bca6c]||_0x1e9e79[_0x3bca6c]['indexOf'](_0x1a0806[_0x1d6f28])===0x0||_0x1a0806[_0x1d6f28]['indexOf'](_0x1e9e79[_0x3bca6c])===0x0){_0x46d0a0++;break;}}}if(_0x46d0a0>=Math['min'](_0x1a0806[_0x41eacf(_0x30d2e5._0x4dba11)],0x3))_0x45d4bd+=0x32;}if(_0x45d4bd>=0x32&&_0x574091&&_0xea8102['indexOf'](_0x574091)>=0x0)_0x45d4bd+=0xa;if(_0x45d4bd>=0x32)_0x2950bc['push']({'doc':_0x3ea9ab,'score':_0x45d4bd});}_0x2950bc[_0x41eacf(_0x30d2e5._0x3de717)](function(_0x14835f,_0x34e38f){return _0x34e38f['score']-_0x14835f['score'];});var _0x4181ad=[];for(var _0x58ee5b=0x0;_0x58ee5b<Math['min'](_0x2950bc['length'],0x5);_0x58ee5b++)_0x4181ad[_0x41eacf(0x14f)](_0x2950bc[_0x58ee5b]['doc']);return _0x4181ad;}function extractAbhilinksUrl(_0x187d86){var _0x11cf52=_0x310f1c,_0x481f78=_0x187d86['match'](/<a[^>]*href="(https:\/\/abhilinks\.(?:life|site)\/[^"]+)"[^>]*class="btn"[^>]*>/i);if(_0x481f78)return _0x481f78[0x1];var _0x971738=_0x187d86[_0x11cf52(0x17d)](/<a[^>]*href="(https:\/\/abhilinks\.(?:life|site)\/[^"]+)"[^>]*>/i);if(_0x971738)return _0x971738[0x1];return null;}function extractQualityOptions(_0x20fe67){var _0x1381f4={_0x4a6234:0x13b,_0x20362c:0x14a,_0x12769a:0x177,_0x104fab:0x185,_0x1d402d:0x138},_0x19a4b3=_0x310f1c,_0x23729e=[],_0x503fcb=/(2160|1080|720|480)[pP](?:\s+\w{1,15})?\s*\[([^\]]+)\]/g,_0x52cacc;while((_0x52cacc=_0x503fcb[_0x19a4b3(_0x1381f4._0x4a6234)](_0x20fe67))!==null){var _0x187712=_0x52cacc[0x1][_0x19a4b3(_0x1381f4._0x20362c)]()+'p',_0x1d7858=_0x52cacc[0x2];if(_0x187712==='480p')continue;var _0x8ad359=_0x52cacc[_0x19a4b3(_0x1381f4._0x12769a)],_0x149d52=_0x20fe67['substring'](Math[_0x19a4b3(_0x1381f4._0x104fab)](0x0,_0x8ad359-0xc8),_0x8ad359+0x258),_0x39b7b3=_0x149d52['match'](/href="(https:\/\/hubcloud\.cx\/(?:drive|video)\/[^"]+)"/i),_0x1ec54e=_0x149d52['match'](/href="(https:\/\/href\.li\/\?https:\/\/vcloud\.zip\/[^"]+)"/i);if(_0x39b7b3)_0x23729e['push']({'quality':_0x187712,'size':_0x1d7858,'type':'hubcloud','url':_0x39b7b3[0x1]});else{if(_0x1ec54e)_0x23729e['push']({'quality':_0x187712,'size':_0x1d7858,'type':_0x19a4b3(_0x1381f4._0x1d402d),'url':_0x1ec54e[0x1]});}}return _0x23729e;}function extractVcloudUrl(_0x4692d9){var _0x323fa6={_0x13d9bc:0x17d},_0x3ff589=_0x310f1c,_0x2d1ca4=_0x4692d9[_0x3ff589(_0x323fa6._0x13d9bc)](/href\.li\/\?https:\/\/vcloud\.zip\/([^"&?]+)/i);if(_0x2d1ca4)return'https://vcloud.zip/'+_0x2d1ca4[0x1];return null;}function processHubcloud(_0x53d57c){var _0x29dded={_0x1b8937:0x190,_0x7e4ecd:0x171,_0x1e1360:0x176};return __async(this,null,function*(){var _0x4e56c7=_0x2f28,_0x66e1d6=yield fetchText(_0x53d57c,{'headers':hdrs({'Referer':abhilinksBase+'/'})});if(!_0x66e1d6)return null;var _0x4af464=_0x66e1d6['match'](/href="(https:\/\/[^"]*hubcloud\.php[^"]*)"/i);if(!_0x4af464)return null;var _0x44815f=_0x4af464[0x1][_0x4e56c7(0x137)](/&amp;/g,'&'),_0x2fd0cb=_0x4e56c7(_0x29dded._0x1b8937),_0x1bad6c=yield fetchText(_0x44815f,{'headers':{'User-Agent':_0x2fd0cb,'Accept':_0x4e56c7(_0x29dded._0x7e4ecd),'Accept-Language':_0x4e56c7(0x135),'Referer':_0x53d57c,'DNT':'1','Cookie':'xla=s4t'}});if(!_0x1bad6c||_0x1bad6c[_0x4e56c7(_0x29dded._0x1e1360)]<0x1f4)return null;return extractFSLLinks(_0x1bad6c);});}function _0x2f28(_0x4047aa,_0x53f8be){_0x4047aa=_0x4047aa-0x123;var _0x16beae=_0x16be();var _0x2f285b=_0x16beae[_0x4047aa];if(_0x2f28['LzjmQW']===undefined){var _0xc5914c=function(_0x1b0fae){var _0xb3db34='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';var _0x1750ab='',_0x374b0d='';for(var _0x425222=0x0,_0x25582f,_0x5b90ea,_0x55645f=0x0;_0x5b90ea=_0x1b0fae['charAt'](_0x55645f++);~_0x5b90ea&&(_0x25582f=_0x425222%0x4?_0x25582f*0x40+_0x5b90ea:_0x5b90ea,_0x425222++%0x4)?_0x1750ab+=String['fromCharCode'](0xff&_0x25582f>>(-0x2*_0x425222&0x6)):0x0){_0x5b90ea=_0xb3db34['indexOf'](_0x5b90ea);}for(var _0x17ebe3=0x0,_0x5dc19c=_0x1750ab['length'];_0x17ebe3<_0x5dc19c;_0x17ebe3++){_0x374b0d+='%'+('00'+_0x1750ab['charCodeAt'](_0x17ebe3)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x374b0d);};_0x2f28['ruJRDY']=_0xc5914c,_0x2f28['EdYqyz']={},_0x2f28['LzjmQW']=!![];}var _0xd9de81=_0x16beae[0x0],_0x3cb9c4=_0x4047aa+_0xd9de81,_0x2c6f23=_0x2f28['EdYqyz'][_0x3cb9c4];return!_0x2c6f23?(_0x2f285b=_0x2f28['ruJRDY'](_0x2f285b),_0x2f28['EdYqyz'][_0x3cb9c4]=_0x2f285b):_0x2f285b=_0x2c6f23,_0x2f285b;}function processVcloud(_0x2103c8){return __async(this,null,function*(){var _0x17ac52=_0x2f28,_0xe77736=yield fetchText(_0x2103c8,{'headers':hdrs({'Referer':abhilinksBase+'/'})});if(!_0xe77736)return null;var _0x55d29d=_0xe77736['match'](/atob\s*\(\s*atob\s*\(\s*['"]([^'"]+)['"]\s*\)\s*\)/);if(!_0x55d29d)return null;var _0x43d203,_0x22cb2a;try{_0x43d203=atob(_0x55d29d[0x1]),_0x22cb2a=atob(_0x43d203);}catch(_0x395319){return null;}var _0x2597d7=yield fetchText(_0x22cb2a,{'headers':hdrs({'Referer':movieshuntBase+'/','Cookie':_0x17ac52(0x178)})});if(!_0x2597d7)return null;return extractFSLLinks(_0x2597d7);});}function extractFSLLinks(_0x325d9b){var _0x3b0ffd={_0x492a8f:0x137,_0x33b0b5:0x174,_0x315366:0x174,_0x2ba6f9:0x174,_0x55f5db:0x16e,_0xb72fea:0x174,_0x3bb4b6:0x132,_0x202d72:0x174,_0x25ea77:0x191,_0x4dedf1:0x14a,_0x48b91d:0x14f},_0x5af520=_0x310f1c,_0x208d5b=[],_0x1b3a38=_0x325d9b[_0x5af520(0x17d)](/<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi);if(!_0x1b3a38)return _0x208d5b;for(var _0x40e07e=0x0;_0x40e07e<_0x1b3a38[_0x5af520(0x176)];_0x40e07e++){var _0x1ad292=_0x1b3a38[_0x40e07e],_0x2e9704=_0x1ad292['match'](/href="([^"]+)"/i),_0x6ea2d4=_0x1ad292['match'](/>([\s\S]*?)<\/a>/i);if(!_0x2e9704)continue;var _0x2f5eb1=_0x2e9704[0x1]['replace'](/&amp;/g,'&'),_0x4e905b=_0x6ea2d4?_0x6ea2d4[0x1][_0x5af520(_0x3b0ffd._0x492a8f)](/<[^>]+>/g,'')['trim']():'';if(!_0x2f5eb1||_0x2f5eb1[_0x5af520(0x123)]('javascript:')===0x0)continue;if(/telegram/i[_0x5af520(0x174)](_0x4e905b)||/tg\//i[_0x5af520(_0x3b0ffd._0x33b0b5)](_0x2f5eb1)||/pixeldrain/i[_0x5af520(_0x3b0ffd._0x315366)](_0x2f5eb1))continue;if(/hubcloud\.cx|gpdl2/i[_0x5af520(0x174)](_0x2f5eb1))continue;var _0x1ba466='';if(/cdn\.fsl-buckets\.life/i['test'](_0x2f5eb1)||/r2\.cloudflarestorage/i['test'](_0x2f5eb1)||/r2\.dev/i[_0x5af520(_0x3b0ffd._0x2ba6f9)](_0x2f5eb1))_0x1ba466=_0x5af520(_0x3b0ffd._0x55f5db);else{if(/hub\.(latent|whistle)/i[_0x5af520(_0x3b0ffd._0xb72fea)](_0x2f5eb1))_0x1ba466=_0x5af520(_0x3b0ffd._0x3bb4b6);else{if(/workers\.dev/i[_0x5af520(_0x3b0ffd._0x202d72)](_0x2f5eb1))_0x1ba466=_0x5af520(_0x3b0ffd._0x25ea77);else continue;}}var _0x41d550='',_0x40aab7=_0x4e905b['match'](/(2160|1080|720|480)\s*[pP]/i);if(_0x40aab7)_0x41d550=_0x40aab7[0x1][_0x5af520(_0x3b0ffd._0x4dedf1)]()+'p';_0x208d5b[_0x5af520(_0x3b0ffd._0x48b91d)]({'url':_0x2f5eb1,'type':_0x1ba466,'quality':_0x41d550,'rawText':_0x4e905b});}return _0x208d5b;}function dedupe(_0x4bf438){var _0x160ba3={_0x41daf6:0x18f},_0x592ea8={_0x2708f3:0x141,_0x2807bd:0x141},_0x1b456c=_0x310f1c,_0x461301={};return(_0x4bf438||[])[_0x1b456c(_0x160ba3._0x41daf6)](function(_0xf9c09c){var _0xbe5ab2=_0x1b456c;if(!_0xf9c09c||!_0xf9c09c[_0xbe5ab2(_0x592ea8._0x2708f3)])return![];if(_0x461301[_0xf9c09c['url']])return![];return _0x461301[_0xf9c09c[_0xbe5ab2(_0x592ea8._0x2807bd)]]=!![],!![];});}function extractEpisodes(_0x2e4c8d){var _0xa7d4ad={_0x3e26a1:0x14f,_0x6116a8:0x13b},_0x7fee0=_0x310f1c,_0x5df0a0=[],_0x399c5c=/-:\s*Episodes?\s*:\s*(\d+)\s*:-/gi,_0x1031cb=[],_0x5dc188;while((_0x5dc188=_0x399c5c[_0x7fee0(0x13b)](_0x2e4c8d))!==null)_0x1031cb[_0x7fee0(_0xa7d4ad._0x3e26a1)]({'num':parseInt(_0x5dc188[0x1]),'idx':_0x5dc188['index']});if(_0x1031cb['length']===0x0){var _0x4f1092=/>\s*Episode\s*(\d+)\s*</gi;while((_0x5dc188=_0x4f1092[_0x7fee0(_0xa7d4ad._0x6116a8)](_0x2e4c8d))!==null)_0x1031cb['push']({'num':parseInt(_0x5dc188[0x1]),'idx':_0x5dc188[_0x7fee0(0x177)]});}for(var _0x4e001d=0x0;_0x4e001d<_0x1031cb[_0x7fee0(0x176)];_0x4e001d++){var _0x152570=_0x1031cb[_0x4e001d][_0x7fee0(0x170)],_0x4df64b=_0x4e001d+0x1<_0x1031cb['length']?_0x1031cb[_0x4e001d+0x1][_0x7fee0(0x170)]:_0x2e4c8d['length'],_0xd81823=_0x2e4c8d[_0x7fee0(0x13a)](_0x152570,_0x4df64b),_0x465b63=[],_0x5051a2=/href="(https:\/\/hubcloud\.cx\/(?:drive|video)\/[^"]+)"/gi,_0x2be59c;while((_0x2be59c=_0x5051a2['exec'](_0xd81823))!==null)_0x465b63['push']({'type':_0x7fee0(0x139),'url':_0x2be59c[0x1]});var _0xfbf45f=/href="(https:\/\/href\.li\/\?https:\/\/vcloud\.zip\/[^"]+)"/gi;while((_0x2be59c=_0xfbf45f['exec'](_0xd81823))!==null){var _0x43559a=extractVcloudUrl(_0x2be59c[0x1]);if(_0x43559a)_0x465b63[_0x7fee0(0x14f)]({'type':_0x7fee0(0x138),'url':_0x43559a});}if(_0x465b63['length'])_0x5df0a0['push']({'number':_0x1031cb[_0x4e001d]['num'],'links':_0x465b63});}return _0x5df0a0;}function extractSeasonLinks(_0x1dcfe6){var _0xf0fc92={_0x4eb7d7:0x177,_0x50b10e:0x176,_0x9ea5ee:0x17d,_0x5ab49c:0x13a,_0x455ca5:0x17d},_0x42784f=_0x310f1c,_0x270685={},_0xfbb9da=/<h4[^>]*>([\s\S]*?)<\/h4>/gi,_0x24646c=[],_0xb06cca;while((_0xb06cca=_0xfbb9da['exec'](_0x1dcfe6))!==null)_0x24646c[_0x42784f(0x14f)]({'inner':_0xb06cca[0x1],'start':_0xb06cca[_0x42784f(0x177)],'end':_0xb06cca[_0x42784f(_0xf0fc92._0x4eb7d7)]+_0xb06cca[0x0][_0x42784f(0x176)]});for(var _0x502eff=0x0;_0x502eff<_0x24646c[_0x42784f(_0xf0fc92._0x50b10e)];_0x502eff++){var _0x1299b2=_0x24646c[_0x502eff],_0x452671=_0x1299b2['inner'][_0x42784f(_0xf0fc92._0x9ea5ee)](/Season\s+(\d+)/i),_0x213cb1=_0x1299b2[_0x42784f(0x13f)]['match'](/(\d+p)/i);if(!_0x452671||!_0x213cb1)continue;var _0x33c6cc=parseInt(_0x452671[0x1]),_0x318229=_0x213cb1[0x1]['toLowerCase'](),_0x515b3a=_0x24646c[_0x502eff]['end'],_0x74b9de=_0x502eff+0x1<_0x24646c[_0x42784f(0x176)]?_0x24646c[_0x502eff+0x1]['start']:_0x1dcfe6['length'],_0x3b2681=_0x1dcfe6[_0x42784f(_0xf0fc92._0x5ab49c)](_0x515b3a,_0x74b9de),_0x331be4=_0x3b2681[_0x42784f(_0xf0fc92._0x455ca5)](/href="(https:\/\/abhilinks\.(?:life|site)\/archives\/\d+)\/?"/i);if(_0x331be4){if(!_0x270685[_0x33c6cc])_0x270685[_0x33c6cc]={};if(!_0x270685[_0x33c6cc][_0x318229])_0x270685[_0x33c6cc][_0x318229]=_0x331be4[0x1];}}return _0x270685;}function parseLanguage(_0xf8242d){var _0x32745b={_0x5187dd:0x15f,_0x8de059:0x156,_0x4e8fa6:0x152,_0x1ab9c7:0x123,_0x50c3a8:0x187},_0x46c742=_0x310f1c,_0x3212f6=String(_0xf8242d||'')['toLowerCase'](),_0x3170a9=['tamil',_0x46c742(_0x32745b._0x5187dd),_0x46c742(_0x32745b._0x8de059),_0x46c742(0x198),'kannada',_0x46c742(_0x32745b._0x4e8fa6),'punjabi'],_0x39de57=0x0;for(var _0x2df865=0x0;_0x2df865<_0x3170a9['length'];_0x2df865++){if(_0x3212f6[_0x46c742(_0x32745b._0x1ab9c7)](_0x3170a9[_0x2df865])!==-0x1)_0x39de57++;}if(_0x39de57>=0x1||_0x3212f6[_0x46c742(0x123)]('multi')!==-0x1)return _0x46c742(_0x32745b._0x50c3a8);if(_0x3212f6[_0x46c742(0x123)](_0x46c742(0x196))!==-0x1||_0x3212f6['indexOf']('hindi')!==-0x1&&_0x3212f6['indexOf']('english')!==-0x1)return'Dual-Audio';return'Dual-Audio';}function buildDropdownMetadata(_0x2540b4,_0x3938c2,_0x3eebc5,_0x39a9a8,_0x492dd4,_0x17f4f6,_0x25a629,_0x58dbe6,_0xef4265){var _0x233868={_0x5bc085:0x130,_0x59a387:0x14e,_0x2d54ca:0x17a,_0x5e5daa:0x12e,_0x14c2fc:0x123,_0x12c8a0:0x144,_0x971a9b:0x17f,_0x2bdfd1:0x123,_0x65d70a:0x124,_0x4f7b77:0x199,_0x8adf0e:0x158,_0x1286a5:0x123,_0x4978b0:0x123,_0x3c94ee:0x168,_0xfa1a19:0x182,_0x52fc18:0x14f,_0x55a12a:0x160,_0xfafe3a:0x167,_0x3d9489:0x131,_0x3041f9:0x123,_0x1315e4:0x153,_0x359870:0x14c,_0x3066e4:0x172,_0x5e21ba:0x12c,_0x565ab5:0x188,_0xe83cc1:0x193},_0x2fe5f2=_0x310f1c,_0x30c874=(_0x492dd4?_0x2540b4[_0x2fe5f2(_0x233868._0x5bc085)]:_0x2540b4[_0x2fe5f2(_0x233868._0x59a387)])||'Unknown\x20Title',_0x141c2a=_0x492dd4?(_0x2540b4[_0x2fe5f2(0x13c)]||'')['split']('-')[0x0]:(_0x2540b4[_0x2fe5f2(_0x233868._0x2d54ca)]||'')['split']('-')[0x0],_0x15e228=_0x141c2a?'\x20('+_0x141c2a+')':'',_0xb426f5=(String(_0x58dbe6)+'\x20'+String(_0xef4265))[_0x2fe5f2(0x14a)](),_0x3c2e97=_0x492dd4?'🎬\x20':_0x2fe5f2(_0x233868._0x5e5daa),_0x36a88b=_0x3c2e97+_0x30c874+_0x15e228;_0x492dd4&&_0x17f4f6!=null&&_0x25a629!=null&&(_0x36a88b+=_0x2fe5f2(0x148)+String(_0x17f4f6)[_0x2fe5f2(0x12a)](0x2,'0')+'\x20E'+String(_0x25a629)[_0x2fe5f2(0x12a)](0x2,'0'));var _0x2db396='💎';if(_0x3938c2[_0x2fe5f2(_0x233868._0x14c2fc)](_0x2fe5f2(_0x233868._0x12c8a0))!==-0x1||_0x3938c2['indexOf']('4k')!==-0x1)_0x2db396='🌟';else{if(_0x3938c2[_0x2fe5f2(_0x233868._0x14c2fc)]('1080')!==-0x1)_0x2db396='🔥';}var _0xe81952=_0xb426f5[_0x2fe5f2(0x17d)](/(\d+(?:\.\d+)?\s*(?:gb|mb))/i),_0x7fbdb=_0xe81952?_0xe81952[0x1][_0x2fe5f2(_0x233868._0x971a9b)]():_0x3eebc5||'Variable\x20Size',_0xbaf3b1=_0x2db396+'\x20'+_0x3938c2+'\x20|\x20💾\x20'+_0x7fbdb,_0x2ab57f='SDR';if(_0xb426f5[_0x2fe5f2(_0x233868._0x2bdfd1)](_0x2fe5f2(_0x233868._0x65d70a))!==-0x1)_0x2ab57f='HDR10+';else{if(_0xb426f5['indexOf'](_0x2fe5f2(_0x233868._0x4f7b77))!==-0x1)_0x2ab57f='HDR10';else{if(_0xb426f5[_0x2fe5f2(_0x233868._0x2bdfd1)](_0x2fe5f2(_0x233868._0x8adf0e))!==-0x1)_0x2ab57f='HDR';}}var _0x2a4c49='';if(_0xb426f5[_0x2fe5f2(0x123)](_0x2fe5f2(0x189))!==-0x1||_0xb426f5[_0x2fe5f2(_0x233868._0x1286a5)]('10-bit')!==-0x1)_0x2a4c49='\x20•\x2010Bit';var _0xf4553e=_0x2fe5f2(0x162);if(_0xb426f5[_0x2fe5f2(0x123)]('hevc')!==-0x1)_0xf4553e='⚡\x20HEVC';else{if(_0xb426f5[_0x2fe5f2(_0x233868._0x4978b0)](_0x2fe5f2(0x166))!==-0x1||_0xb426f5['indexOf']('h265')!==-0x1)_0xf4553e=_0x2fe5f2(0x186);}var _0x5b5a90=_0xef4265[_0x2fe5f2(0x123)]('.mp4')!==-0x1?'MP4':_0x2fe5f2(_0x233868._0x3c94ee),_0x17a161=_0x2fe5f2(0x143)+_0x2ab57f+_0x2a4c49+'\x20|\x20'+_0xf4553e+'\x20|\x20📦\x20'+_0x5b5a90,_0x4798cc=parseLanguage(_0xb426f5),_0x5819bf=[];if(_0xb426f5['indexOf'](_0x2fe5f2(_0x233868._0xfa1a19))!==-0x1||_0xb426f5[_0x2fe5f2(0x123)]('ddp\x205.1')!==-0x1)_0x5819bf[_0x2fe5f2(_0x233868._0x52fc18)]('DDP5.1');if(_0xb426f5['indexOf']('truehd')!==-0x1)_0x5819bf['push'](_0x2fe5f2(_0x233868._0x55a12a));if(_0xb426f5[_0x2fe5f2(0x123)]('dd5.1')!==-0x1||_0xb426f5['indexOf'](_0x2fe5f2(0x136))!==-0x1){if(_0x5819bf['indexOf']('DDP5.1')===-0x1)_0x5819bf['push'](_0x2fe5f2(_0x233868._0xfafe3a));}_0x5819bf[_0x2fe5f2(0x176)]===0x0&&_0x5819bf[_0x2fe5f2(0x14f)](_0x2fe5f2(0x195));var _0x4f648b=_0x5819bf[_0x2fe5f2(0x126)](_0x2fe5f2(_0x233868._0x3d9489)),_0x19840c=_0xb426f5[_0x2fe5f2(_0x233868._0x3041f9)](_0x2fe5f2(_0x233868._0x1315e4))!==-0x1?_0x2fe5f2(0x15c):'',_0x34f959=_0x2fe5f2(_0x233868._0x359870)+_0x4798cc+_0x2fe5f2(_0x233868._0x3066e4)+_0x4f648b+_0x19840c,_0x4a18c5=_0x2fe5f2(_0x233868._0x5e21ba);if(_0xb426f5[_0x2fe5f2(0x123)](_0x2fe5f2(0x13e))!==-0x1||_0xb426f5[_0x2fe5f2(0x123)](_0x2fe5f2(0x18a))!==-0x1)_0x4a18c5=_0x2fe5f2(_0x233868._0x565ab5);else{if(_0xb426f5[_0x2fe5f2(0x123)]('bluray')!==-0x1)_0x4a18c5='💿\x20Blu-Ray';}var _0x491e25=_0x2fe5f2(_0x233868._0xe83cc1)+(_0x39a9a8||'FSL')+_0x2fe5f2(0x18c)+_0x4a18c5;return _0x36a88b+'\x0a'+_0xbaf3b1+'\x0a'+_0x17a161+'\x0a'+_0x34f959+'\x0a'+_0x491e25;}function getStreams(_0x4eaad3,_0x54ad2f,_0x47391e,_0x3af7cd){var _0x4c0c61={_0x4b2692:0x159,_0x4b6244:0x194,_0x1d633e:0x183,_0x2de632:0x176,_0x4c91a:0x18e,_0xede543:0x197,_0x5d8f1d:0x175,_0x1f52c5:0x16c,_0x8c230b:0x176,_0x2534e4:0x192,_0x128ddf:0x176,_0x3f9876:0x180,_0x9d4b59:0x141,_0x2f6303:0x173,_0x2cd511:0x18c,_0x5f3bca:0x14d,_0x3d8cac:0x14b,_0xbdc23a:0x141,_0xc36a42:0x14f,_0x1268d2:0x16c,_0x16c8b0:0x163,_0x4a0f0c:0x129};return __async(this,null,function*(){var _0x55280c={_0x543986:0x14a,_0x4d6e91:0x16d},_0x4a0b41=_0x2f28;currentUA=UAS[Math[_0x4a0b41(0x145)](Math[_0x4a0b41(0x155)]()*UAS['length'])],log('getStreams('+_0x4eaad3+',\x20'+_0x54ad2f+',\x20'+_0x47391e+',\x20'+_0x3af7cd+')');var _0x1d261e=_0x54ad2f==='tv'||_0x54ad2f==='series',_0x559f11=yield getTMDBInfo(_0x4eaad3,_0x54ad2f);if(!_0x559f11)return log('TMDB\x20fetch\x20failed'),[];var _0x48efd9=_0x1d261e?_0x559f11['name']:_0x559f11[_0x4a0b41(0x14e)];if(!_0x48efd9)return log(_0x4a0b41(_0x4c0c61._0x4b2692)),[];log(_0x4a0b41(_0x4c0c61._0x4b6244)+_0x48efd9);var _0x28eb64=yield searchSite(_0x48efd9);if(!_0x28eb64||!_0x28eb64['length'])return log(_0x4a0b41(_0x4c0c61._0x1d633e)),[];log('Search\x20results:\x20'+_0x28eb64['length']);var _0x38c2d1=matchHits(_0x28eb64,_0x559f11,_0x1d261e);if(!_0x38c2d1[_0x4a0b41(_0x4c0c61._0x2de632)])return log('No\x20match\x20found'),[];log(_0x4a0b41(_0x4c0c61._0x4c91a)+_0x38c2d1[_0x4a0b41(_0x4c0c61._0x2de632)]);for(var _0x5a23b5=0x0;_0x5a23b5<_0x38c2d1['length'];_0x5a23b5++){let _0x15d98d=function(_0x11a14c){var _0x2ff857=_0x4a0b41,_0x8fb4e7=_0x11a14c[_0x2ff857(_0x55280c._0x543986)]();if(_0x8fb4e7['indexOf']('2160p')!==-0x1||_0x8fb4e7[_0x2ff857(0x123)]('4k')!==-0x1)return 0x870;if(_0x8fb4e7[_0x2ff857(0x123)](_0x2ff857(_0x55280c._0x4d6e91))!==-0x1)return 0x438;if(_0x8fb4e7['indexOf']('720p')!==-0x1)return 0x2d0;if(_0x8fb4e7['indexOf']('480p')!==-0x1)return 0x1e0;return 0x0;};var _0xf73bc6=_0x15d98d,_0x577933=_0x38c2d1[_0x5a23b5],_0x22a0ab=_0x577933['url'];log(_0x4a0b41(0x140)+_0x22a0ab);var _0x1a6162=yield fetchText(_0x22a0ab,{'headers':hdrs()});if(!_0x1a6162)continue;var _0x18a46d=[];if(_0x1d261e){var _0xc7baca=_0x47391e!==void 0x0&&_0x47391e!==null&&_0x47391e!==_0x4a0b41(_0x4c0c61._0xede543)?parseInt(_0x47391e):null,_0x17d273=_0x3af7cd!==void 0x0&&_0x3af7cd!==null&&_0x3af7cd!=='undefined'?parseInt(_0x3af7cd):null,_0x2240f8=[];if(_0xc7baca){var _0x2a618e=extractSeasonLinks(_0x1a6162);if(_0x2a618e[_0xc7baca]){var _0x29427b=Object[_0x4a0b41(_0x4c0c61._0x5d8f1d)](_0x2a618e[_0xc7baca])[_0x4a0b41(_0x4c0c61._0x1f52c5)](function(_0xaa4366,_0x109acb){return parseInt(_0x109acb)-parseInt(_0xaa4366);});_0x29427b['forEach'](function(_0x1b2eae){var _0x40fcec=_0x4a0b41;_0x2240f8[_0x40fcec(0x14f)]({'quality':_0x1b2eae,'url':_0x2a618e[_0xc7baca][_0x1b2eae]});}),log('S'+_0xc7baca+'\x20qualities:\x20'+_0x29427b[_0x4a0b41(0x126)](',\x20'));}}if(!_0x2240f8[_0x4a0b41(0x176)]){var _0x397b2c=extractAbhilinksUrl(_0x1a6162);if(_0x397b2c)_0x2240f8[_0x4a0b41(0x14f)]({'quality':'','url':_0x397b2c});}if(!_0x2240f8['length']){log('No\x20abhilinks\x20URLs,\x20trying\x20next\x20match');continue;}var _0x2f8b07=[];for(var _0xe8c940=0x0;_0xe8c940<_0x2240f8['length'];_0xe8c940++){var _0x508206=_0x2240f8[_0xe8c940];log('Fetching\x20'+(_0x508206['quality']||'default')+':\x20'+_0x508206[_0x4a0b41(0x141)]);var _0x119a5f=yield fetchText(_0x508206[_0x4a0b41(0x141)],{'headers':hdrs()});if(!_0x119a5f){log(_0x4a0b41(0x128));continue;}var _0x3c8677=extractEpisodes(_0x119a5f);if(!_0x3c8677[_0x4a0b41(_0x4c0c61._0x8c230b)]){log('\x20\x20no\x20episodes');continue;}var _0x1aecaf=_0x3c8677;if(_0x17d273){_0x1aecaf=_0x3c8677[_0x4a0b41(0x18f)](function(_0x70348b){return _0x70348b['number']===_0x17d273;});if(!_0x1aecaf[_0x4a0b41(0x176)]){log('\x20\x20episode\x20'+_0x17d273+'\x20not\x20found');continue;}}for(var _0x468cdf=0x0;_0x468cdf<_0x1aecaf['length'];_0x468cdf++){var _0xbf76d9=_0x1aecaf[_0x468cdf];for(var _0x493863=0x0;_0x493863<_0xbf76d9[_0x4a0b41(0x192)]['length'];_0x493863++){var _0x51e685=_0xbf76d9[_0x4a0b41(_0x4c0c61._0x2534e4)][_0x493863];_0x2f8b07['push'](function(_0x109088,_0x4274d7,_0x2636b4){var _0x517c5b={_0x177b73:0x173};return function(){var _0x4f6a8c={_0x4f48ef:0x14b};return __async(this,null,function*(){var _0x5d22fb=_0x2f28,_0x3e6ce7=null;if(_0x4274d7['type']==='hubcloud')_0x3e6ce7=yield processHubcloud(_0x4274d7[_0x5d22fb(0x141)]);else{if(_0x4274d7[_0x5d22fb(_0x517c5b._0x177b73)]===_0x5d22fb(0x138))_0x3e6ce7=yield processVcloud(_0x4274d7['url']);}return _0x3e6ce7&&_0x3e6ce7['forEach'](function(_0x4bfed7){var _0x3b60ef=_0x5d22fb;_0x4bfed7['episode']=_0x109088,_0x4bfed7[_0x3b60ef(_0x4f6a8c._0x4f48ef)]=_0x4bfed7['quality']||_0x2636b4;}),_0x3e6ce7;});};}(_0xbf76d9['number'],_0x51e685,_0x508206[_0x4a0b41(0x14b)]));}}}if(!_0x2f8b07[_0x4a0b41(_0x4c0c61._0x128ddf)]){log(_0x4a0b41(_0x4c0c61._0x3f9876));continue;}log('Processing\x20'+_0x2f8b07['length']+'\x20hubcloud/vcloud\x20links...');var _0x2ad642=yield Promise['all'](_0x2f8b07['map'](function(_0x17c2e4){return _0x17c2e4();}));for(var _0x38c39d=0x0;_0x38c39d<_0x2ad642['length'];_0x38c39d++){if(!_0x2ad642[_0x38c39d])continue;for(var _0x2f1a14=0x0;_0x2f1a14<_0x2ad642[_0x38c39d][_0x4a0b41(0x176)];_0x2f1a14++){var _0x1be39f=_0x2ad642[_0x38c39d][_0x2f1a14],_0x47b640=(_0x1be39f[_0x4a0b41(0x14b)]||'')['toLowerCase']();if(_0x47b640==='480p'||_0x47b640==='hd')continue;var _0x59b4d2=_0x47b640||_0x4a0b41(0x16d),_0x28ea33=(_0x1be39f['rawText']||'')+'\x20'+_0x1be39f[_0x4a0b41(_0x4c0c61._0x9d4b59)],_0x4c389f=parseLanguage(_0x28ea33),_0x8ec37b=buildDropdownMetadata(_0x559f11,_0x59b4d2,'',_0x1be39f[_0x4a0b41(_0x4c0c61._0x2f6303)],!![],_0xc7baca,_0x1be39f['episode'],_0x28ea33,_0x1be39f[_0x4a0b41(_0x4c0c61._0x9d4b59)]);_0x18a46d[_0x4a0b41(0x14f)]({'name':PROVIDER_NAME+_0x4a0b41(_0x4c0c61._0x2cd511)+_0x59b4d2+_0x4a0b41(_0x4c0c61._0x2cd511)+_0x4c389f,'title':_0x8ec37b,'size':_0x8ec37b,'description':_0x8ec37b,'url':_0x1be39f[_0x4a0b41(0x141)],'quality':'','language':'','headers':{'Referer':movieshuntBase+'/','User-Agent':currentUA}});}}}else{var _0xdafffd=extractAbhilinksUrl(_0x1a6162);if(!_0xdafffd){log('No\x20abhilinks\x20URL,\x20trying\x20next\x20match');continue;}log('Abhilinks:\x20'+_0xdafffd);var _0x119a5f=yield fetchText(_0xdafffd,{'headers':hdrs()});if(!_0x119a5f){log(_0x4a0b41(0x169));continue;}var _0x1ef9b7=extractQualityOptions(_0x119a5f);if(!_0x1ef9b7[_0x4a0b41(_0x4c0c61._0x128ddf)]){log('No\x20quality\x20options\x20found');continue;}log('Quality\x20options:\x20'+_0x1ef9b7['length']);var _0x509d32=[];for(var _0x253041=0x0;_0x253041<_0x1ef9b7['length'];_0x253041++){var _0x52c1cf=_0x1ef9b7[_0x253041];_0x509d32['push'](function(_0x4ee6a2){var _0x1e2843={_0x3d0a87:0x141};return function(){return __async(this,null,function*(){var _0x4acf5b=_0x2f28;if(_0x4ee6a2[_0x4acf5b(0x173)]==='hubcloud')return yield processHubcloud(_0x4ee6a2['url']);else{if(_0x4ee6a2['type']==='vcloud'){var _0x1dda2b=extractVcloudUrl(_0x4ee6a2[_0x4acf5b(_0x1e2843._0x3d0a87)]);if(!_0x1dda2b)return null;return yield processVcloud(_0x1dda2b);}}return null;});};}(_0x52c1cf));}var _0x49b302=yield Promise[_0x4a0b41(_0x4c0c61._0x5f3bca)](_0x509d32['map'](function(_0x5369f0){return _0x5369f0();}));for(var _0x1af6e8=0x0;_0x1af6e8<_0x49b302['length'];_0x1af6e8++){if(!_0x49b302[_0x1af6e8])continue;var _0x3d2802=_0x1ef9b7[_0x1af6e8];for(var _0x1a2da9=0x0;_0x1a2da9<_0x49b302[_0x1af6e8][_0x4a0b41(0x176)];_0x1a2da9++){var _0x1d7dd6=_0x49b302[_0x1af6e8][_0x1a2da9],_0x50492a=(_0x1d7dd6[_0x4a0b41(_0x4c0c61._0x3d8cac)]||_0x3d2802[_0x4a0b41(0x14b)]||'')['toLowerCase']();if(_0x50492a===_0x4a0b41(0x15e)||_0x50492a==='hd')continue;var _0x59b4d2=_0x50492a||'1080p',_0x4eed6b=_0x3d2802['size']||'',_0x28ea33=(_0x1d7dd6[_0x4a0b41(0x16b)]||'')+'\x20'+_0x1d7dd6[_0x4a0b41(_0x4c0c61._0xbdc23a)]+'\x20'+_0x4eed6b,_0x4c389f=parseLanguage(_0x28ea33),_0x8ec37b=buildDropdownMetadata(_0x559f11,_0x59b4d2,_0x4eed6b,_0x1d7dd6['type'],![],null,null,_0x28ea33,_0x1d7dd6[_0x4a0b41(0x141)]);_0x18a46d[_0x4a0b41(_0x4c0c61._0xc36a42)]({'name':'🏹\x20'+PROVIDER_NAME+_0x4a0b41(_0x4c0c61._0x2cd511)+_0x59b4d2+'\x20|\x20'+_0x4c389f,'title':_0x8ec37b,'size':_0x8ec37b,'description':_0x8ec37b,'url':_0x1d7dd6['url'],'quality':'','language':'','headers':{'Referer':movieshuntBase+'/','User-Agent':currentUA}});}}}_0x18a46d=dedupe(_0x18a46d),_0x18a46d[_0x4a0b41(_0x4c0c61._0x1268d2)](function(_0x4c9389,_0x8a7a04){var _0xc86f46=_0x4a0b41;return _0x15d98d(_0x8a7a04['name'])-_0x15d98d(_0x4c9389[_0xc86f46(0x130)]);});if(_0x18a46d['length']>0x0)return log('Returning\x20'+_0x18a46d[_0x4a0b41(_0x4c0c61._0x8c230b)]+_0x4a0b41(_0x4c0c61._0x16c8b0)+_0x22a0ab),_0x18a46d;log(_0x4a0b41(_0x4c0c61._0x4a0f0c));}return log('No\x20streams\x20from\x20any\x20match'),[];});}typeof module!=='undefined'&&module[_0x310f1c(0x165)]?module['exports']={'getStreams':getStreams}:global['getStreams']=getStreams;
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:a16e67d169c3 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"movieshunt","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"failClosedUnknown":false,"defaultUserAgent":"","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"scoped-playback-context-v4"});
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
/* NUVIO_GLOBAL_STREAM_IDENTITY_V1:a9973b907e32 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"movieshunt","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"cross-client-positive-mismatch-anime-confirmed-v3"});
/* NUVIO_GLOBAL_STREAM_PRESENTATION_V1:88375900e102 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"movieshunt","tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","tmdbTimeoutMs":1200,"implementationRevision":"all-providers-facts-badge-dedupe-tmdb-fallback-v9"});
