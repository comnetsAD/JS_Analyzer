-- phpMyAdmin SQL Dump
-- version 4.9.0.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Sep 18, 2019 at 05:35 AM
-- Server version: 8.0.16
-- PHP Version: 7.1.23

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `JSCleaner`
--

-- --------------------------------------------------------

--
-- Table structure for table `caching`
--

CREATE TABLE `caching` (
  `id` int(11) NOT NULL,
  `url` varchar(10000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `filename` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `caching`
--

INSERT INTO `caching` (`id`, `url`, `filename`) VALUES
(290, 'http://yasirzaki.net/', '9886e7e04cf2bbe34f0a4b17276249'),
(291, 'https://fonts.googleapis.com:443/css?family=Droid+Sans%3A400%2C700%7CRoboto%3A300italic%2C400%2C700%2C900&subset=latin', 'ab46717802a86b3bb6af248c6cc101'),
(292, 'http://yasirzaki.net/wp-content/plugins/gallery-plugin/css/frontend_style.css?ver=4.9.11', '36ba89f2d227ac7763c90665133cf3'),
(293, 'http://yasirzaki.net/wp-content/themes/identity/js/skip-link-focus-fix.js?ver=20130115', '840ccf74bedfa2a2e026b4bb2e9427'),
(294, 'http://yasirzaki.net/wp-content/plugins/papercite/papercite.css?ver=4.9.11', '6e26226a3568a6774074031770e8c7'),
(295, 'http://yasirzaki.net/wp-content/plugins/vertical-news-scroller/css/newsscrollcss.css', '43cf6dc5906afa1ff975157b8ced42'),
(296, 'http://yasirzaki.net/wp-includes/js/jquery/jquery.js?ver=1.12.4', '91951bd5a9e621c0b5008ea890c05a'),
(297, 'http://yasirzaki.net/wp-content/plugins/contact-form-plugin/css/form_style.css?ver=4.0.9', 'b0ddf808c4b1aa3f7eafc007dbe7aa'),
(298, 'http://yasirzaki.net/wp-content/plugins/papercite/js/papercite.js?ver=4.9.11', '46653690db5e807d91ed5a8b5a0a69'),
(299, 'http://yasirzaki.net/wp-content/themes/identity/genericons/genericons.css?ver=3.3.0', '859907d9c4bdef9c8f3c349325d693'),
(300, 'http://yasirzaki.net/wp-content/themes/identity/style.css?ver=4.9.11', '6566821ac6bf4a8eac202e507b752d'),
(301, 'http://yasirzaki.net/wp-content/themes/identity/js/navigation.js?ver=20120206', 'af1416e17a8316b77daca408b57568'),
(302, 'http://yasirzaki.net/wp-includes/js/wp-embed.min.js?ver=4.9.11', '48123ea4e5169ca570f1d1cb5acff8'),
(303, 'http://yasirzaki.net/wp-includes/css/dashicons.min.css?ver=4.9.11', 'fe357afd65043749b9e5f119adfb59'),
(304, 'http://yasirzaki.net/wp-includes/js/jquery/jquery-migrate.min.js?ver=1.4.1', '3ba809ecf8f4a9d64023a529fb96de'),
(305, 'http://yasirzaki.net/wp-content/themes/identity/js/identity.js?ver=20150504', 'd7a930ee9ec24c8c30a1193d5e22ae'),
(306, 'http://yasirzaki.net/wp-content/plugins/google-analytics-for-wordpress/assets/js/frontend.min.js?ver=7.0.5', 'c1f719a14b0322f30e215d725b2ed9'),
(307, 'http://yasirzaki.net/wp-content/plugins/gallery-plugin/fancybox/jquery.fancybox.min.css?ver=4.9.11', 'b672fff0d5106e67a83023549314b1'),
(308, 'http://yasirzaki.net/wp-includes/js/wp-emoji-release.min.js?ver=4.9.11', '391ab09b436fd4bc75f13ac9e42a11'),
(309, 'http://yasirzaki.net/wp-content/themes/identity/genericons/genericons/genericons.css', 'b3815b5bd626b33d2d54c7e4f3bda8'),
(310, 'https://fonts.gstatic.com:443/s/droidsans/v10/SlGWmQWMvZQIdix7AFxXmMh3eDs1ZyHKpWg.woff2', 'd2b4afc30c7d07bbbf51535d9a00bc'),
(311, 'https://fonts.gstatic.com:443/s/roboto/v20/KFOlCnqEu92Fr1MmWUlfBBc4AMP6lQ.woff2', 'e74836144ee199c3082d2583fa4ea9'),
(312, 'https://fonts.gstatic.com:443/s/droidsans/v10/SlGVmQWMvZQIdix7AFxXkHNSbRYXags.woff2', '32a529486990107d41d5944ea13e58'),
(313, 'http://sites.nyuad.nyu.edu/dtl/projects/ghanaweb/thumbs.jpg', '94c82e329882898c9c25af7f8de507'),
(314, 'http://yasirzaki.net/wp-content/uploads/2015/05/verus2.png', 'efdf2e609678707fe3256fda6011d5'),
(315, 'http://yasirzaki.net/wp-content/uploads/2018/07/alcc.jpg', '5bedd8c86d9b8cdb91e1d246d7a236'),
(316, 'http://yasirzaki.net/wp-content/uploads/2018/05/IMG_20180323_144752-e1531229063227-572x520.jpg', '01ba31f29328ace68e4b76ac1f3984'),
(317, 'http://yasirzaki.net/wp-content/uploads/2017/12/cropped-DSC_0060-Edit-5.jpg', '4d746edfec458902af5ff3bce1edcb'),
(318, 'http://yasirzaki.net/wp-content/uploads/2018/12/gaius.jpg', '8b3a54cf105dd651c3f6f7b149fc08'),
(319, 'https://www.google-analytics.com:443/analytics.js', 'fe04eafee7a3c0001b3b0927be9a03'),
(320, 'http://yasirzaki.net/wp-content/uploads/2013/10/cropped-photo-192x192.jpg', '757908ac8da9b1fba3740762d2af02'),
(321, 'http://yasirzaki.net/wp-content/uploads/2013/10/cropped-photo-32x32.jpg', '7b7a2de3d02c418794738b77642d0f'),
(322, 'https://www.google-analytics.com:443/r/collect?v=1&_v=j79&a=1439688978&t=pageview&_s=1&dl=http%3A%2F%2Fyasirzaki.net%2F&ul=en-us&de=UTF-8&dt=Assistant%20professor%20at%20NYU%20Abu%20Dhabi&sd=24-bit&sr=1680x1050&vp=1680x485&je=0&_u=QACAAUABC~&jid=1173474209&gjid=971328494&cid=1910151817.1568653366&tid=UA-41639738-2&_gid=740472165.1568653366&_r=1&z=1283137749', '3e69e6cf3e790147e373c93230a2f4'),
(323, 'https://fonts.googleapis.com:443/css?family=Droid+Sans%3A400%2C700|Roboto%3A300italic%2C400%2C700%2C900&subset=latin', 'a96c833c1dd01b8ce2144c9cfe6d98'),
(324, 'https://fonts.googleapis.com:443/favicon.ico', '1a190a5a5b9df157e3aa0c702137bf'),
(325, 'http://www.yasirzaki.net/', '405ea05800f93dd42da4c432c96b93'),
(326, 'https://www.google.com:443/complete/search?client=firefox&q=ya', 'e7145d2fc86273e99c1d140de99fd9'),
(327, 'https://tiles.services.mozilla.com:443/v4/links/activity-stream', '2d0bf2fa497e76a3bad88d1c6b57b5'),
(328, 'http://detectportal.firefox.com/success.txt', 'cd764ec0a3c2cea7891d574f8c7976'),
(329, 'http://detectportal.firefox.com/success.txt?ipv4', '685e6f2e1b543a42b5da76b71b05bb'),
(330, 'http://detectportal.firefox.com/success.txt?ipv6', 'e3606f65a1a7810c29eeb50f098724'),
(331, 'https://incoming.telemetry.mozilla.org:443/submit/telemetry/098cf9ef-7736-cc40-8ddf-135651332cc4/event/Firefox/69.0/release/20190827005903?v=4', '0cc2fc0ba26dd8671d80395d7c3548'),
(332, 'https://incoming.telemetry.mozilla.org:443/submit/telemetry/f7e3ffda-152f-ef45-9aa6-79508d4278ac/health/Firefox/69.0/release/20190827005903?v=4', 'e255f05dc31937cb4c1a2dc11cf577'),
(333, 'https://www.irs.gov:443/', '8d5138770997cf5a4344a61822e197'),
(334, 'https://static.addtoany.com:443/menu/page.js', '0a9756a7855101e792847006bdb6ec'),
(335, 'https://www.irs.gov:443/pub/google_tag/google_tag.script.js?pwx15a', '4781e5e580769aca95af6e7ce5f009'),
(336, 'https://www.irs.gov:443/pub/css/css_mbEdPJit2a_rSEJu-pfZeztFtyMKwys3wFfb4Cz5BPw.css?pwx15a', '94d2ba713dc853007d5b4cec176e09'),
(337, 'https://www.irs.gov:443/pub/js/js_JL5-xpD24I600Ahcw5Q4vP2Cfa69VcdR4zEsiFjClFY.js', '2d6a69080285e87f45f789cc453756'),
(338, 'https://www.irs.gov:443/pub/css/css_CZ92nQsAd-B5ldkmrbS1AQO0e0J-SF6PTVf06RC2Rfg.css?pwx15a', '8b17995d8bb02c589d377b4434dece'),
(339, 'https://www.irs.gov:443/pub/css/css_7UnKMjxjKJQkSvoopWLh5UkbeczRYpmKFEy2vfvL0kI.css?pwx15a', '7ca96c53a985d4b1949685502dc30a'),
(340, 'https://www.irs.gov:443/pub/css/css_Lu8_Y4xqA7-VPL1fo7drI8S9NzHQjQ4xGPzTh9IzPd4.css?pwx15a', '84c242b113772fe213555ab1b7d573'),
(341, 'https://www.irs.gov:443/static_assets/js/reporting/autotracker.js', '727772f2a919c4cc897ff4ce390f1e'),
(342, 'https://www.irs.gov:443/pub/empty.js', '21f88c23be6ff2e06e42eb3ea85f57'),
(343, 'https://www.irs.gov:443/pub/js/js_8NOdCA8pCNRYZgBTuyniXst9j0Sl8ZjduZEscEqgSww.js', '389bfb150499f611c991d8f3743555'),
(344, 'https://www.irs.gov:443/static_assets/js/libs/jquery.min.js', 'b03a816cc9f550b4a9d92a6975dadd'),
(345, 'https://www.irs.gov:443/pub/js/js_2-5N7bibuHd526nWts1udSPBKwwsymcBcxtElPV00Xg.js', '864973b408795964e6af319ba7130b'),
(346, 'https://www.youtube.com:443/iframe_api', 'bf7854b1eb639fb6161bdf88333554'),
(347, 'https://www.youtube.com:443/embed/zy5pb7Cp1-0?autoplay=0&start=0&rel=0', 'e68735e05b2e00d8f0df3d0c9e558b'),
(348, 'https://s.go-mpulse.net:443/boomerang/YVPKX-K5D8K-83D3W-U8X45-X3FTN', 'd8e93755ea9e90830735e14dd5b3bb'),
(349, 'https://s.ytimg.com:443/yts/jsbin/www-widgetapi-vfl1ao7_O/www-widgetapi.js', '79b01199367b89f02c6ceb9e2edc0e'),
(350, 'https://www.youtube.com:443/embed/zy5pb7Cp1-0?autoplay=0&start=0&rel=0&enablejsapi=1&origin=https://www.irs.gov', 'c596000b61e0fa74245f2b2ec49465'),
(351, 'https://www.irs.gov:443/themes/custom/pup_base/logo.svg', '5d8144cde8c768a13280640a01508c'),
(352, 'https://www.irs.gov:443/themes/custom/pup_irs/images/logo-print.svg', 'b7d78e4949f46364e0ece070a9cf64'),
(353, 'https://www.youtube.com:443/yts/jsbin/www-embed-player-vfljq-ciQ/www-embed-player.js', 'c5f6f4b143468c66ccaa1d020d0331'),
(354, 'https://www.youtube.com:443/yts/cssbin/www-player-2x-vflRXH7Q_.css', 'b57956a08e5921437574e159819dd1'),
(355, 'https://www.irs.gov:443/static_assets/js/reporting/google-analytics.js', '2aafb82df0580d6f9913bd6d889b66'),
(356, 'https://www.youtube.com:443/yts/jsbin/player_ias-vfl8E5RS_/en_US/base.js', '4029c3f4c8247509b209fa47fdae5e'),
(357, 'https://www.irs.gov:443/static_assets/js/leftnav/height.js', 'aa2ea81029ab9c1c55c3591c5f3ddc'),
(358, 'https://www.irs.gov:443/static_assets/js/reporting/federated-analytics.js?agency=Treasury&subagency=IRS&sdor=true', '67200921403ceda893ff2ba17ed972'),
(359, 'https://www.irs.gov:443/pub/image/Sized_Refunds_image_60.jpg', '0cbf89de1aa8afd080819a678b45a3'),
(360, 'https://c.go-mpulse.net:443/api/config.json?key=YVPKX-K5D8K-83D3W-U8X45-X3FTN&d=www.irs.gov&t=5228990&v=1.571.0&if=&sl=0&si=z53usqgksb-NaN&plugins=AK,ConfigOverride,Continuity,PageParams,IFrameDelay,AutoXHR,SPA,Angular,Backbone,Ember,History,RT,CrossDomain,BW,PaintTiming,NavigationTiming,ResourceTiming,Memory,CACHE_RELOAD,Errors,TPAnalytics,UserTiming,LOGN&acao=', '493ee49b9324f651ba0b4574b326f1'),
(361, 'https://www.google.com:443/js/bg/Gl0-vewO4Yd4U_1vEyKck8QcaE6Ctlbu9T3leF98kLk.js', '1015f8a087fe423fc6a13bb00aad99'),
(362, 'https://www.youtube.com:443/yts/jsbin/player_ias-vfl8E5RS_/en_US/remote.js', 'a7cf5612d0262fa9c7f29914f19081'),
(363, 'https://i.ytimg.com:443/vi/zy5pb7Cp1-0/maxresdefault.jpg', 'b9412d5dfe2525d269f65939fabe10'),
(364, 'https://yt3.ggpht.com:443/-mAitnR_g0V4/AAAAAAAAAAI/AAAAAAAAAAA/HtbMD94MVws/s68-c-k-no-mo-rj-c0xffffff/photo.jpg', 'a26f40de070df9b43a21a09a780c78'),
(365, 'https://googleads.g.doubleclick.net:443/pagead/id', 'f5f6973604295895b366b1fe60d147'),
(366, 'https://fonts.gstatic.com:443/s/roboto/v18/KFOlCnqEu92Fr1MmEU9fBBc4AMP6lQ.woff2', 'bc37e39a5d69731e3fb0e074e057e2'),
(367, 'https://www.youtube.com:443/generate_204?c8Y7DQ', 'ff1842065f717a411c52f7d3183add'),
(368, 'https://static.doubleclick.net:443/instream/ad_status.js', '1db4477e5af7e36134fa9f26b175fd'),
(369, 'https://www.irs.gov:443/static_assets/js/https.js', 'bb4bd1b2b8ad425d902a7f7f95c12a'),
(370, 'https://www.irs.gov:443/modules/contrib/we_megamenu/assets/fonts/fontquicksand/quicksand-v6-latin-700.woff2', 'f491d88f3f6b8b57c030c59af60aac'),
(371, 'https://www.irs.gov:443/modules/contrib/we_megamenu/assets/fonts/fontquicksand/quicksand-v6-latin-regular.woff2', '059fba4f541b8ca66fd1057d1cfce8'),
(372, 'https://www.irs.gov:443/themes/custom/pup_base/fonts/source-sans-pro/fonts/sourcesanspro-bold-webfont.woff', '1b2b62c7e50a906f2c1c57623803dc'),
(373, 'https://www.irs.gov:443/themes/custom/pup_base/fonts/source-sans-pro/fonts/sourcesanspro-regular-webfont.woff', '24df28caf44ec76e03631b5d874e9d'),
(374, 'https://www.irs.gov:443/themes/custom/pup_base/fonts/glyphicons-halflings-regular.woff2', '63363bdb2a893f1385a3eebc1e481b'),
(375, 'https://www.irs.gov:443/pub/image/tax-withholding-estimator-screenshot-1a.jpg', '86b81ab798a93724d9bdadc54e6918'),
(376, 'https://www.irs.gov:443/themes/custom/pup_base/fonts/fontawesome-webfont.woff2?v=4.7.0', 'af187001c53e3803a559bfeda6d787'),
(377, 'https://www.irs.gov:443/system/files/2018-06/AmericanFlagPROD.jpg', '99229bbcdb3d01a4288c2fef8b8191'),
(378, 'https://www.irs.gov:443/pub/image/IRS2Go_cropped_0.jpg', '1276bc2c333ff519553dfd7c591d09'),
(379, 'https://www.irs.gov:443/pub/image/umbrellas_disaster-prep-hp-370x200_0.jpg', '6bbae1ce3286b606a06e170424260c'),
(380, 'https://www.irs.gov:443/pub/image/free-file-homepage.jpg', '33324f7637c253109ed90397eae145'),
(381, 'https://platform.twitter.com:443/widgets.js', '8dcafd4f17d6105c157ef034488943'),
(382, 'https://www.irs.gov:443/themes/custom/pup_base/images/irs_horiz-01.svg', '0dc36a4365e9541c56a163c467f757'),
(383, 'https://www.irs.gov:443/pub/image/couple-homepage-370x200.jpg', '3c16cc3ce9753533279ec3a1ef7fe1'),
(384, 'https://platform.twitter.com:443/widgets/widget_iframe.d9084ca5af1ffbe01c8d444cfadfa6fe.html?origin=https%3A%2F%2Fwww.irs.gov', 'c04d137a680807acf1f0ef156ff8f0'),
(385, 'https://www.irs.gov:443/pub/irs_horiz_logo%20%281%29.svg', 'fa7fefd5e572b77eaf8e3cd0021d45'),
(386, 'https://www.irs.gov:443/pub/image/calendar-homepage-370x200.jpg', '1fed79bee61adcd9e0db5f45d2653e'),
(387, 'https://platform.twitter.com:443/js/tweet.8f3cd35f6a21b1943f48b734e9d7613c.js', '15c240908866a323de35fa4c27ff7c'),
(388, 'https://platform.twitter.com:443/js/moment~timeline~tweet.3fd6099de8eff1ea82d1c2e6aaae7f2a.js', 'ebfefbdc50bb684c9fe81f1fc4f1af'),
(389, 'https://www.irs.gov:443/pub/image/refund_woman-homepage-370x200_0.jpg', '48fb7f451ffb83fcd28ce25338f22f'),
(390, 'https://www.google-analytics.com:443/plugins/ua/linkid.js', '39a9ddb3a83201020423f028eb71b3'),
(391, 'https://cdn.syndication.twimg.com:443/tweets.json?callback=__twttr.callbacks.cb0&ids=1172525841919762433-c&lang=en&suppress_response_codes=true&theme=light&tz=GMT%2B0400', '7e1561da3d913b393678287fec42f1'),
(392, 'https://platform.twitter.com:443/css/tweet.9bf5093a19cec463852b31b784bf047a.light.ltr.css', 'ccea9ef7e8e9c20e36c52280df3e35'),
(393, 'https://syndication.twitter.com:443/settings', '5ea986fcbd6beefc92961f4c2bdda0'),
(394, 'https://www.google-analytics.com:443/r/collect?v=1&_v=j79&a=1999520550&t=pageview&_s=1&dl=https%3A%2F%2Fwww.irs.gov%2F&ul=en-us&de=UTF-8&dt=Internal%20Revenue%20Service%20%7C%20An%20official%20website%20of%20the%20United%20States%20government&sd=24-bit&sr=1680x1050&vp=1429x485&je=0&_u=SCCAAEAj~&jid=1791772686&gjid=878400448&cid=215897630.1561531539&tid=UA-22588183-6&_gid=935031326.1568652441&_r=1&cd1=NULL&cd2=NULL&cd5=NULL&cd6=58476&z=1413320211', '46413634280e45f58ab12b61178c4e'),
(395, 'https://www.google-analytics.com:443/r/collect?v=1&_v=j79&aip=1&a=1999520550&t=pageview&_s=1&dl=https%3A%2F%2Fwww.irs.gov%2F&dp=%2F&ul=en-us&de=UTF-8&dt=Internal%20Revenue%20Service%20%7C%20An%20official%20website%20of%20the%20United%20States%20government&sd=24-bit&sr=1680x1050&vp=1429x485&je=0&_u=SCCAAUAj~&jid=1635137610&gjid=1248351618&cid=215897630.1561531539&tid=UA-33523145-1&_gid=935031326.1568652441&_r=1&cd1=TREASURY&cd2=TREASURY%20-%20IRS&cd5=unspecified%3Airs.gov&cd3=20160520%20v3.1%20-%20Universal%20Analytics&cd4=unspecified%3Airs.gov&z=565054036', '38cd77782c9be919f15a195e4be785'),
(396, 'https://www.irs.gov:443/themes/custom/pup_base/favicon.ico', '3db580cb56050fb95a85aed5afcbe5'),
(397, 'https://pbs.twimg.com:443/profile_images/459325990980694017/HNbdQu_v_bigger.jpeg', '62000db6c226b354b53e785de71ca8'),
(398, 'https://js-agent.newrelic.com:443/nr-1130.min.js', '18820a88b08ec39c1f152db6a486a2'),
(399, 'https://safebrowsing.googleapis.com:443/v4/fullHashes:find?$ct=application/x-protobuf&key=AIzaSyC7jsptDS3am4tPx4r3nxis7IMjBc5Dovo&$httpMethod=POST&$req=ChUKE25hdmNsaWVudC1hdXRvLWZmb3gSGwoNCAUQBhgBIgMwMDEwARC1lgcaAhgDC-hmGRouCAUQBBoGCgQrmo3FGgYKBGpRRokaBgoElDWQYRoGCgSlAr4NGgYKBKk8o1IgAQ==', 'febbbefabc95d31ee855af27f326c4'),
(400, 'https://syndication.twitter.com:443/i/jot', 'a13e6702f8f2d20d7d78b63561c6ad'),
(401, 'https://platform.twitter.com:443/jot.html', '8cf93e9b42577b4534cf42521cb5cf'),
(402, 'https://bam.nr-data.net:443/1/b67fc6a152?a=70700070&v=1130.54e767a&to=blMHY0AHDUcDUEZQWFcZJFRGDwxaTXdATEdYWjlSXBIKQBtCR1xCXGomWFwSEVsOX1dLa3xYEV5GHzJBB0ZXbH56WQtDQAkPWAdBHwdWWlUAREE%3D&rst=33057&ref=https://www.irs.gov/&ap=137&be=26215&fe=32697&dc=28258&perf=%7B%22timing%22:%7B%22of%22:1568697057124,%22n%22:0,%22u%22:26206,%22ue%22:26207,%22f%22:25209,%22dn%22:25247,%22dne%22:25247,%22c%22:25247,%22s%22:0,%22ce%22:25247,%22rq%22:25247,%22rp%22:25870,%22rpe%22:26204,%22dl%22:0,%22di%22:20,%22ds%22:21,%22de%22:26,%22dc%22:32696,%22l%22:32696,%22le%22:32701%7D,%22navigation%22:%7B%7D%7D&at=QhQEFQgdHkk%3D&jsonp=NREUM.setToken', '803dd877c186da9428a41888d18ed4'),
(403, 'https://www.youtube.com:443/youtubei/v1/log_event?alt=json&key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8', '4e32632127b729cebfb0a2f5280b68'),
(404, 'https://www.irs.gov:443/js.html', 'irs.gov');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `caching`
--
ALTER TABLE `caching`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `caching`
--
ALTER TABLE `caching`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=405;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
