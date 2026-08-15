const _0xf741e1=_0x2887;(function(_0x304ad9,_0x44115a){const _0x3e16ff={_0x32d8aa:0x1de,_0x42cdc4:0x214,_0x861482:0x205,_0xb988b1:0x1d3,_0x2b46cb:0x1f7,_0x1f23a8:0x1fb,_0x3e1e14:0x1ee},_0x34545a=_0x2887,_0x3c5ad8=_0x304ad9();while(!![]){try{const _0x1de960=-parseInt(_0x34545a(_0x3e16ff._0x32d8aa))/0x1+parseInt(_0x34545a(_0x3e16ff._0x42cdc4))/0x2*(parseInt(_0x34545a(0x1cc))/0x3)+-parseInt(_0x34545a(_0x3e16ff._0x861482))/0x4*(parseInt(_0x34545a(_0x3e16ff._0xb988b1))/0x5)+-parseInt(_0x34545a(0x201))/0x6+-parseInt(_0x34545a(_0x3e16ff._0x2b46cb))/0x7*(-parseInt(_0x34545a(_0x3e16ff._0x1f23a8))/0x8)+-parseInt(_0x34545a(_0x3e16ff._0x3e1e14))/0x9*(parseInt(_0x34545a(0x20c))/0xa)+-parseInt(_0x34545a(0x1fe))/0xb;if(_0x1de960===_0x44115a)break;else _0x3c5ad8['push'](_0x3c5ad8['shift']());}catch(_0x1a6883){_0x3c5ad8['push'](_0x3c5ad8['shift']());}}}(_0x3133,0xcdd99));var __async=(_0x2d675e,_0x60c5d2,_0x4d995e)=>{return new Promise((_0x4625d3,_0x318b22)=>{const _0x3ca796=_0x2887;var _0x2208ac=_0x3e7f5a=>{try{_0x4a8699(_0x4d995e['next'](_0x3e7f5a));}catch(_0x548bed){_0x318b22(_0x548bed);}},_0x27dcf1=_0x1e6249=>{try{_0x4a8699(_0x4d995e['throw'](_0x1e6249));}catch(_0x39c42){_0x318b22(_0x39c42);}},_0x4a8699=_0x278d21=>_0x278d21['done']?_0x4625d3(_0x278d21[_0x3ca796(0x216)]):Promise['resolve'](_0x278d21[_0x3ca796(0x216)])[_0x3ca796(0x1d6)](_0x2208ac,_0x27dcf1);_0x4a8699((_0x4d995e=_0x4d995e['apply'](_0x2d675e,_0x60c5d2))['next']());});},cheerio=require(_0xf741e1(0x1f5)),BASE_URL=_0xf741e1(0x1f3),TMDB_API_KEY=_0xf741e1(0x1ca),BROWSER_UA=_0xf741e1(0x20d),HEADERS={'User-Agent':BROWSER_UA,'Referer':BASE_URL+'/'},PLAYBACK_HEADERS={'User-Agent':BROWSER_UA,'Referer':'https://urlshortlink.top/','Origin':'https://urlshortlink.top'};function _0x3133(){const _0x43fded=['mtG2nwy0m2eWntq5y2e1mgqZndfKzdLHyJHImJLMndK','ic0G','m1Lot01mDq','zgL2lNzPzgvVlxrODw1IigLTzW','DxjS','CMvWBgfJzq','nZiWCa','lM0ZDtG','vw5RBM93BIbuAxrSzq','nuvjBLvvCa','zxjYB3i','C3rHCNrZv2L0Aa','DgHLBG','zw5NBgLZAa','zxbPC29Kzv9YDw5FDgLTzq','DgvSDwD1','ihWG4O+X77Ipia','DhjPBq','mta4ma','yxr0CG','odK2nduZvwngAfDt','Ahr0Chm6lY9HCgKUDgHLBw92AwvKyI5VCMCVmY8','w0zPyLDHDgnOxq','Cg9WDxa','8j+oNU+4JYa','vgfTAwW','zMLUza','Dw5KzwzPBMvK','rw5NBgLZAcdIGkiGsgLUzgK','Dg9mB3DLCKnHC2u','4PQRiezPyLDHDgnOihWG','Bwf0y2G','BMfTzq','Bg9Hza','Aw5WDxqJDMLKzw8TAwq','zhvHBa','mtm4mZn6BuH5zhu','ywrK','u2LUz2XLluf1zgLV','ChvZAa','DgL0Bgu','Ahr0Chm6lY9MAwj3yxrJAc5HCNq','ANnVBG','y2HLzxjPBY13AxrOB3v0lw5VzguTBMf0AxzL','BxvSDgK','mta3ody5nZL0v1LNzNq','tI9b','ndGW','Ahr0Ca','ofnysvvZqG','rhvHBc1bDwrPBW','BgvUz3rO','ntqWmJiZmMXOA1rXwG','lM1Wna','DxjSpwH0Dha','mtu2mZiZnhr4zgTSta','zxHWB3j0CW','DgfTAwW','8j+oRca','mtC5odG1nKDSC3Dqyq','jNbHz2vFAwq9mq','qMfUz2XH','Dgv4Da','Aw5JBhvKzxm','vw5RBM93BG','sgLUzgK','nJuWqxzzyLvb','tw96AwXSys81lJaGkeXPBNv4oYbbBMrYB2LKideWoYblksbbChbSzvDLyKTPDc81mZCUmZyGkeTive1mlcbSAwTLieDLy2TVksbdAhjVBwuVmtm3lJaUmc4Wie1VyMLSzsbtywzHCMKVntm3lJm2','l2fQyxGVzxbPC29KzxmUCgHWp3zPzgvVx2LKpq','yMfUz2XH','C29YDa','CxvHBgL0Eq','CNvUDgLTzq','zwfJAa','mJK5otC3nfPNtfP1sq','mJe2ma','DMfSDwu','ndGWCa','mZyW','AhjLzG','ic0GuW'];_0x3133=function(){return _0x43fded;};return _0x3133();}function extractQuality(_0x4af06e){const _0x2a1bf5={_0x1845bf:0x209,_0x287843:0x209,_0x846d66:0x1d0,_0x5618bd:0x1f9,_0x1139ad:0x217,_0x368115:0x218},_0x3d3eb7=_0xf741e1,_0x364bfd=(_0x4af06e||'')[_0x3d3eb7(0x1e7)]();if(_0x364bfd['includes'](_0x3d3eb7(0x215))||_0x364bfd[_0x3d3eb7(_0x2a1bf5._0x1845bf)]('4k'))return'4K';if(_0x364bfd['includes'](_0x3d3eb7(0x1dc)))return'1080p';if(_0x364bfd[_0x3d3eb7(_0x2a1bf5._0x287843)]('720'))return _0x3d3eb7(_0x2a1bf5._0x846d66);if(_0x364bfd[_0x3d3eb7(0x209)](_0x3d3eb7(_0x2a1bf5._0x5618bd)))return _0x3d3eb7(_0x2a1bf5._0x1139ad);if(_0x364bfd['includes'](_0x3d3eb7(_0x2a1bf5._0x368115)))return'360p';return'Unknown';}function parseStreamFromShortenerHtml(_0x472691){const _0x1a0a70={_0x5861aa:0x1eb},_0x17f5a5={_0x2ee33e:0x200},_0x1d6725=_0xf741e1;if(!_0x472691)return null;const _0x30fbd7=cheerio[_0x1d6725(_0x1a0a70._0x5861aa)](_0x472691);let _0x37aa7e=_0x30fbd7('a.hidden-button.buttonDownloadnew')['attr'](_0x1d6725(0x219));!_0x37aa7e&&_0x30fbd7('a')['each']((_0x439235,_0x3862d7)=>{const _0xd3d77c=_0x1d6725,_0x58c50c=_0x30fbd7(_0x3862d7)['attr']('href')||'';if(_0x58c50c[_0xd3d77c(0x209)](_0xd3d77c(_0x17f5a5._0x2ee33e)))return _0x37aa7e=_0x58c50c,![];});if(!_0x37aa7e){const _0x34e4f4=/https?:\/\/[^\s"'`<>]+?\.b-cdn\.net\/[^\s"'`<>]+\.(?:mkv|mp4|m3u8)/i,_0x2d5b16=_0x472691['match'](_0x34e4f4);if(_0x2d5b16)return _0x2d5b16[0x0];}if(_0x37aa7e){let _0x88d123=_0x37aa7e[_0x1d6725(0x1cf)](/.*url=/,'')[_0x1d6725(0x1db)]();return decodeURIComponent(_0x88d123);}return null;}function _0x2887(_0x4265b4,_0x56ac93){_0x4265b4=_0x4265b4-0x1ca;const _0x3133cd=_0x3133();let _0x2887f5=_0x3133cd[_0x4265b4];if(_0x2887['OuoIzx']===undefined){var _0x23b500=function(_0xc211e8){const _0x691c83='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=';let _0x2d675e='',_0x60c5d2='';for(let _0x4d995e=0x0,_0x4625d3,_0x318b22,_0x2208ac=0x0;_0x318b22=_0xc211e8['charAt'](_0x2208ac++);~_0x318b22&&(_0x4625d3=_0x4d995e%0x4?_0x4625d3*0x40+_0x318b22:_0x318b22,_0x4d995e++%0x4)?_0x2d675e+=String['fromCharCode'](0xff&_0x4625d3>>(-0x2*_0x4d995e&0x6)):0x0){_0x318b22=_0x691c83['indexOf'](_0x318b22);}for(let _0x27dcf1=0x0,_0x4a8699=_0x2d675e['length'];_0x27dcf1<_0x4a8699;_0x27dcf1++){_0x60c5d2+='%'+('00'+_0x2d675e['charCodeAt'](_0x27dcf1)['toString'](0x10))['slice'](-0x2);}return decodeURIComponent(_0x60c5d2);};_0x2887['AbAXzg']=_0x23b500,_0x2887['OaEwku']={},_0x2887['OuoIzx']=!![];}const _0x40b69d=_0x3133cd[0x0],_0x210662=_0x4265b4+_0x40b69d,_0x577b8d=_0x2887['OaEwku'][_0x210662];return!_0x577b8d?(_0x2887f5=_0x2887['AbAXzg'](_0x2887f5),_0x2887['OaEwku'][_0x210662]=_0x2887f5):_0x2887f5=_0x577b8d,_0x2887f5;}function generateStreamLayout(_0x45cde5,_0x473df8,_0x2ff13b,_0x2d85c1,_0x53b7b1,_0x1d9781,_0x17799c){const _0x29894e={_0x2fe9f9:0x1f2,_0x41c336:0x1ea,_0x196abd:0x1f0,_0x2be5bf:0x20b,_0x370a1e:0x1ed,_0x199945:0x209,_0x5a1598:0x1fc,_0x4a1384:0x1e6,_0x28a840:0x20f,_0xd2358c:0x207,_0xb3c17b:0x1ff,_0x1b61c7:0x215,_0x5a9bb5:0x1e8,_0x4cd2b3:0x1da},_0x5a8af3=_0xf741e1;var _0x35e15c;const _0x50c4cc=_0x2d85c1[_0x5a8af3(_0x29894e._0x2fe9f9)]||_0x2d85c1[_0x5a8af3(_0x29894e._0x41c336)]||_0x5a8af3(0x1d2),_0x4888ca=_0x2d85c1['release_date']||_0x2d85c1['first_air_date']||'',_0x10b4de=_0x4888ca?_0x4888ca['split']('-')[0x0]:_0x5a8af3(0x1f8),_0x1bded7=_0x45cde5['toLowerCase']();let _0x493a43=_0x5a8af3(_0x29894e._0x196abd),_0x574513=_0x5a8af3(_0x29894e._0x2be5bf);if(_0x1bded7['includes'](_0x5a8af3(_0x29894e._0x370a1e))||_0x1bded7[_0x5a8af3(_0x29894e._0x199945)]('hindi')&&_0x1bded7[_0x5a8af3(_0x29894e._0x199945)]('english'))_0x493a43=_0x5a8af3(_0x29894e._0x5a1598),_0x574513=_0x5a8af3(_0x29894e._0x4a1384);else{if(_0x1bded7['includes'](_0x5a8af3(0x1f6)))_0x493a43='Multi-Audio',_0x574513='Multilingual';else{if(_0x1bded7['includes'](_0x5a8af3(_0x29894e._0x28a840)))_0x574513=_0x5a8af3(_0x29894e._0xd2358c);else{if(_0x1bded7['includes'](_0x5a8af3(0x203)))_0x574513=_0x5a8af3(0x1e3);else{if(_0x1bded7['includes'](_0x5a8af3(0x1d9)))_0x574513='Telugu';else _0x1bded7['includes'](_0x5a8af3(0x1d7))&&(_0x493a43='Single-Audio',_0x574513='English');}}}}let _0x138764='MKV';if(_0x1bded7['includes'](_0x5a8af3(_0x29894e._0xb3c17b)))_0x138764='MP4';if(_0x1bded7[_0x5a8af3(0x209)](_0x5a8af3(0x1d1)))_0x138764='M3U8\x20/\x20HLS';let _0x19f49d='N/A';_0x53b7b1?_0x19f49d=((_0x35e15c=_0x2d85c1['episode_run_time'])==null?void 0x0:_0x35e15c[0x0])?_0x2d85c1[_0x5a8af3(0x1d8)][0x0]+'\x20min':'45\x20min':_0x19f49d=_0x2d85c1['runtime']?_0x2d85c1[_0x5a8af3(0x212)]+'\x20min':_0x5a8af3(0x1f8);const _0x148fca=_0x2ff13b[_0x5a8af3(_0x29894e._0x199945)]('4K')||_0x2ff13b['includes'](_0x5a8af3(_0x29894e._0x1b61c7))?'🌟':'💎',_0xcd946a=_0x5a8af3(_0x29894e._0x5a9bb5)+_0x2ff13b+'\x20|\x20'+_0x493a43,_0x164663=_0x53b7b1?_0x5a8af3(0x204)+_0x50c4cc+_0x5a8af3(0x21a)+_0x1d9781+'E'+_0x17799c+'\x20('+_0x10b4de+')':'🎬\x20'+_0x50c4cc+_0x5a8af3(0x1cb)+_0x10b4de,_0x4f061e=_0x148fca+'\x20'+_0x2ff13b+'\x20|\x20🌍\x20'+_0x574513,_0x1cafb5=_0x5a8af3(0x1e2)+_0x138764+_0x5a8af3(_0x29894e._0x4cd2b3)+_0x19f49d+'\x20|\x20📌\x20WEB-DL',_0x25d63e=_0x164663+'\x0a'+_0x4f061e+'\x0a'+_0x1cafb5;return{'name':_0xcd946a,'title':_0x25d63e,'url':_0x45cde5,'quality':_0x2ff13b,'behaviorHints':{'notWebReady':![]},'headers':PLAYBACK_HEADERS};}function getStreams(_0x9bd952,_0x573dbc,_0x416797,_0x4f77c3){const _0x152d3a={_0x357efe:0x1df,_0x785b2a:0x206,_0x5c6740:0x208,_0x2dd1d2:0x213,_0x145d07:0x1ce,_0x2ec064:0x1ec,_0x1b51b8:0x20e,_0x5cb22:0x1e9,_0x59e7da:0x1fa,_0x45218e:0x208,_0x56ca69:0x1f4,_0x51b616:0x1ce,_0x1fa55c:0x1ef,_0x165469:0x1ce,_0x51d278:0x210,_0x547997:0x1d4,_0x5933d7:0x1e0},_0x378f2c={_0x5930f6:0x1db,_0x3b8fb7:0x1fa,_0x881890:0x20a},_0x3b9d35={_0x14d194:0x1dd,_0x1c89f6:0x1cd};return __async(this,null,function*(){const _0x498ec3=_0x2887;try{const _0xab14ae=_0x498ec3(_0x152d3a._0x357efe)+_0x573dbc+'/'+_0x9bd952+'?api_key='+TMDB_API_KEY,_0x5b3da3=yield(yield fetch(_0xab14ae))['json'](),_0x19d996=_0x5b3da3['title']||_0x5b3da3['name'];if(!_0x19d996)return[];const _0x3b3a96=BASE_URL+'/search?keyword='+encodeURIComponent(_0x19d996)+_0x498ec3(_0x152d3a._0x785b2a),_0x221f78=yield(yield fetch(_0x3b3a96,{'headers':HEADERS}))[_0x498ec3(_0x152d3a._0x5c6740)](),_0x24832c=cheerio['load'](_0x221f78),_0x3da328=[];_0x24832c('div.video-thumb')[_0x498ec3(_0x152d3a._0x2dd1d2)]((_0x4491ab,_0x134ea3)=>{const _0x2a16cb=_0x498ec3,_0x3479ee=_0x24832c('a',_0x134ea3)[_0x2a16cb(_0x3b9d35._0x14d194)]('href'),_0x5050c8=_0x24832c('p.hptag',_0x134ea3)['text']()['trim']()||_0x24832c(_0x2a16cb(_0x3b9d35._0x1c89f6),_0x134ea3)[_0x2a16cb(_0x3b9d35._0x14d194)]('alt')||'';if(_0x3479ee)_0x3da328[_0x2a16cb(0x1f1)]({'title':_0x5050c8,'url':_0x3479ee});});if(!_0x3da328['length'])return[];const _0x240ce8=_0x573dbc==='tv',_0x5e59b5=_0x19d996['toLowerCase']();let _0x423ee6=_0x3da328[_0x498ec3(0x1e4)](_0x45e521=>_0x45e521[_0x498ec3(0x1f2)][_0x498ec3(0x1e7)]()[_0x498ec3(0x209)](_0x5e59b5));if(!_0x423ee6)_0x423ee6=_0x3da328[0x0];const _0x2b02bd=_0x423ee6[_0x498ec3(_0x152d3a._0x145d07)]['startsWith'](_0x498ec3(0x1fa))?_0x423ee6['url']:''+BASE_URL+_0x423ee6['url'],_0x1e5c29=yield(yield fetch(_0x2b02bd,{'headers':HEADERS}))[_0x498ec3(0x208)](),_0x154bdb=cheerio[_0x498ec3(0x1eb)](_0x1e5c29),_0x3ff341=_0x154bdb(_0x498ec3(_0x152d3a._0x2ec064))['attr']('value');if(!_0x3ff341)return[];const _0x5ee2f0=[],_0x180a66=_0x4f2ccd=>__async(this,null,function*(){const _0x276398=_0x498ec3;for(const _0x5d7537 of _0x4f2ccd){let _0x3bf558=(_0x5d7537['url']||'')[_0x276398(_0x378f2c._0x5930f6)]();if(!_0x3bf558)continue;!_0x3bf558['startsWith'](_0x276398(0x1fa))&&(_0x3bf558=''+BASE_URL+_0x3bf558);const _0xad5265=extractQuality(_0x5d7537['res']||_0x3bf558);if(_0x3bf558[_0x276398(0x1e9)](/\.(mp4|mkv|m3u8)/i))_0x5ee2f0[_0x276398(0x1f1)]({'url':_0x3bf558,'quality':_0xad5265});else try{const _0x40602e=yield(yield fetch(_0x3bf558,{'headers':HEADERS}))['text'](),_0x564a9f=parseStreamFromShortenerHtml(_0x40602e);if(_0x564a9f&&_0x564a9f[_0x276398(0x1d5)](_0x276398(_0x378f2c._0x3b8fb7))){const _0xf57535=extractQuality(_0x564a9f)!==_0x276398(_0x378f2c._0x881890)?extractQuality(_0x564a9f):_0xad5265;_0x5ee2f0[_0x276398(0x1f1)]({'url':_0x564a9f,'quality':_0xf57535});}}catch(_0x1ecc2b){}}});if(_0x240ce8){const _0x3eaa2e=BASE_URL+_0x498ec3(_0x152d3a._0x1b51b8)+_0x3ff341,_0x5cfa0e=yield(yield fetch(_0x3eaa2e,{'headers':HEADERS}))['json'](),_0x4fd45b=_0x5cfa0e['episodes']||[];if(!_0x4fd45b['length'])return[];let _0x87078e='';for(const _0x2a8eef of _0x4fd45b){const _0x31f08d=(_0x2a8eef['title']||'')[_0x498ec3(0x1e7)](),_0x2b8c5a=_0x31f08d[_0x498ec3(_0x152d3a._0x5cb22)](/s(\d{1,2})e(\d{1,3})/);if(_0x2b8c5a){const _0x5419ab=parseInt(_0x2b8c5a[0x1]),_0xbc3e00=parseInt(_0x2b8c5a[0x2]);if(_0x5419ab===_0x416797&&_0xbc3e00===_0x4f77c3){_0x87078e=_0x2a8eef[_0x498ec3(0x1ce)]?_0x2a8eef[_0x498ec3(_0x152d3a._0x145d07)][_0x498ec3(0x1d5)]('http')?_0x2a8eef['url']:''+BASE_URL+_0x2a8eef[_0x498ec3(0x1ce)]:'';break;}}}!_0x87078e&&_0x4fd45b[_0x498ec3(0x1fd)]>0x0&&(_0x87078e=_0x4fd45b[0x0]['url']?_0x4fd45b[0x0][_0x498ec3(0x1ce)]['startsWith'](_0x498ec3(_0x152d3a._0x59e7da))?_0x4fd45b[0x0]['url']:''+BASE_URL+_0x4fd45b[0x0]['url']:'');if(!_0x87078e)return[];const _0x4be846=yield(yield fetch(_0x87078e,{'headers':HEADERS}))[_0x498ec3(_0x152d3a._0x45218e)](),_0x259da0=cheerio[_0x498ec3(0x1eb)](_0x4be846),_0x588d93=_0x259da0('input#video-id')['attr']('value');if(_0x588d93){const _0x1a82ec=BASE_URL+'/ajax/resolution_switcher.php?video_id='+_0x588d93,_0x53c6fc=yield(yield fetch(_0x1a82ec,{'headers':HEADERS}))[_0x498ec3(0x1f4)](),_0x529c64=[..._0x53c6fc['current']||[],..._0x53c6fc[_0x498ec3(0x1e1)]||[]];yield _0x180a66(_0x529c64);}}else{const _0x439a72=BASE_URL+'/ajax/resolution_switcher.php?video_id='+_0x3ff341,_0x26760a=yield(yield fetch(_0x439a72,{'headers':HEADERS}))[_0x498ec3(_0x152d3a._0x56ca69)](),_0x184dd3=[..._0x26760a['current']||[],..._0x26760a['popup']||[]];yield _0x180a66(_0x184dd3);}const _0x803de4=[],_0x3dd978=new Set();for(const _0x2740e8 of _0x5ee2f0){if(!_0x3dd978['has'](_0x2740e8[_0x498ec3(_0x152d3a._0x51b616)])){_0x3dd978[_0x498ec3(_0x152d3a._0x1fa55c)](_0x2740e8['url']);const _0x1d86da=generateStreamLayout(_0x2740e8[_0x498ec3(_0x152d3a._0x165469)],_0x19d996,_0x2740e8[_0x498ec3(0x211)],_0x5b3da3,_0x240ce8,_0x416797,_0x4f77c3);_0x803de4[_0x498ec3(0x1f1)](_0x1d86da);}}const _0xc548d8={'4K':0x5,'1080p':0x4,'720p':0x3,'480p':0x2,'360p':0x1,'Unknown':0x0};return _0x803de4[_0x498ec3(_0x152d3a._0x51d278)]((_0x18dc1a,_0x57bf79)=>{const _0x475003=_0xc548d8[_0x18dc1a['quality']]||0x0,_0x2c32c2=_0xc548d8[_0x57bf79['quality']]||0x0;return _0x2c32c2-_0x475003;}),_0x803de4;}catch(_0x54ae18){return console[_0x498ec3(_0x152d3a._0x547997)](_0x498ec3(_0x152d3a._0x5933d7),_0x54ae18),[];}});}typeof module!==_0xf741e1(0x1e5)&&module[_0xf741e1(0x202)]&&(module[_0xf741e1(0x202)]={'getStreams':getStreams});




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
/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:c3863d077611 */
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
})(typeof globalThis!=="undefined"?globalThis:this,{"providerId":"fibwatch","timeoutMs":6500,"tmdbTimeoutMs":4500,"maxRows":4,"minDurationRatio":0.55,"maxDurationRatio":1.8,"durationIdentity":false,"strictPlayback":false,"tmdbKey":"1865f43a0549ca50d341dd9ab8b29f49","implementationRevision":"platform-playback-context-v3"});
