# delete_unitpic_folders.ps1
# Run from the ROOT of your haniproperties.com repo (where images\unitpic lives)
#
# USAGE:
#   .\delete_unitpic_folders.ps1            -> DRY RUN (shows what would be deleted)
#   .\delete_unitpic_folders.ps1 -Force     -> ACTUALLY DELETES the folders

param(
    [switch]$Force
)

$BaseDir = "images\unitpic"

if (-not (Test-Path $BaseDir)) {
    Write-Host "ERROR: '$BaseDir' not found in current directory." -ForegroundColor Red
    Write-Host "cd into the root of your haniproperties.com repo and try again."
    exit 1
}

$Folders = @(
"conezionresidencesFPR","pangsapuriperdanaMMN","koiprimaADL","mhplatinum2ADL","kristalheightsHF",
"pangsapuribukitbaruEX","pangsapuriindahmasEX","oneequineADL","125richresidenceADL","palmaperakARL",
"bayuresidensisrigombakADL","wismaakarEX","wismaakarupperfloorEX","villariacondominiumEX","villamakmurcondominiumMMN",
"parkviewserviceapartmentEX","maximresidencesADL","flattamanmelatiADL","theheritageresidenceADL","opalresidenceADL",
"greenparkresidenceADL","koitropikaADL","apartmentarenashamelinADL","triobysetiaMMN","sentrovueapartmentADL",
"platinumougresidenceADL","gaiaresidencesADL","tamanbaktiflatEX","saujanapuchongEXP","pangsapuricempakabukitpuchong2NS",
"tamanbukitindahEX","sentulutamacondominiumEX","sentulpointsuiteapartmentEX","o2residenceADL","flattamanbaktiEX",
"residensipandanmas2EX","tamanputraEX","srijelatekADL","serikasturimalayonlyADL","residensijalilmasmalaysianonlyADL",
"ixoraapartmentADL","desaputracondominiumblockaADL","singlestoreyterracess12malaysianonlyADL","maximcitylightsEX","lakefronthomesMMN",
"unitedpointresidencesADL","miharjaapartmentEX","kltraderssquareADL","dvervainresidencesmalaysianonlyADL","vistatasikcondominiumEX",
"suterapinesNS","suriacourtADL","skyawani1ADL","regentgardenADL","danaumurnicondominiumEX",
"apartmentblok21ADL","zentroresidencesMMN","mutiaracondominiumEXP","floraresidencyADL","thezizzdamansaranorthMMN",
"thescottgardensohoADL","arenaresidensi1MMN","antaraapartmentEX","2storeyterracedhousepuncakalamHF","28boulevardADL",
"1razakmansionADL","sd2apartmentADL","ascendaresidencesskyarenaADL","apartmentpermaiputeraEXP","pangsapurijayaMMN",
"ampangprimaEX","libertyarcADL","lakeparkresidenceklnorthADL","sriintan1ADL","residensiadelia4NS",
"brunsfieldriverviewMMN","serojaapartmentNS","ppa1mbukitjalilNS","boulevardEX","alamsanjungsubangwestMMN",
"vistalavenderADL","moscarADL","sriputramasADL","residensiadelia4MMN","sriputramas1EX",
"puriaiyuMMN","idamancahaya2MMN","icityiresidenceMMN","flatsrisabah3aEX","vistasentulresidenceADL",
"triopermaiADL","residensikepongmas2ADL","thezizzADL","tamanbukitkenanganNS","moriresidenceADL",
"razakcityresidencesADL","desamutiaraMMN","thebirchADL","residensibistariaADL","lsh33sentulADL",
"palmgardenMMN","neodamansaraADL","rampaicourtEXP","cengalcondominiumEX","savvyrianadutamasADL",
"flatdanaukotaADL","ecoskyADL","tasikheightsapartmentEX","pangsapurisegarperdanaEX","kepongsentralcondominiumEX",
"apartmentmahkota1EX","seribaiduriHF","puncakserikelanaMMN","puteribayuapartmentNS","gayaresorthomesMMN",
"cerradosouthvillecityNS","angkasacondominiumEXP","theheronresidencyNS","platinumcasadanauADL","desatasikfasa6bADL",
"tasikheightsapartmentADL","seritopazMMN","residensiwangsamasADL","putraresidenceADL","nadayu801ADL",
"ecograndeurgrahamgarden2storeyterraceADL","permaidamansaradamaiHF","seksyen232storeyterraceMMN","puncakbestari2puncakalam2storeyterraceADL","pelangidamansarasentralADL",
"pangsapurisegarperdanaADL","midfieldssungaibesiADL","greenparkresidenceMMN","flatpknsseksyen8NS","angkasacondominiumADL",
"162residencyADL","quinnresidenceFPR","merantihillparkpuncakalam2storeyterraceHF","menarau2MMN","hennaresidencethequartzFPR",
"gayaapartmentFPR","cantararesidenceFPR","amanputrisungaibuloh2storeyterraceHF","altrisresidencethequartzFPR","residensivierraADL",
"radiusbusinessparkLRH","ppa1mselasihAA","parkviewservicedapartmentLRH","pangsapurisegarperdanaNS","pangsapurimentariADL",
"pangsapurialambudimanEX","ougparklaneSHU","metacityNS","kasuarinaapartmentEX","dutaparkresidenceNLH",
"apartmentpuchongpermata1ADL","angkasacondominiumsNS","168parkselayangADL","lakefronthomesDPM","tamanmajusatu2storeyterraceADL",
"tamangreenwoodgombak1tingkatterraceEX","pangsapuriopalADL","lagoonperdanaapartmentADL","dalamandaADL","becentralicityADL",
"bandarmahkotabantingjalanangkasasinglestoreyNS","seiringresidensidamaisuriaMMN","idamancahayaHF","tiaraeastresidence2EX","tamansribayusinglestoreysemidNS",
"suriaindustrialparkDPM","isuiteNS","bandarbukitrajajalanastakasinglestoreyterracecornerADL","99residenceEX","theheritageresidenceEX",
"theelementsEX","sripelangiEXP","sentulvillagecondominiumEX","reizzresidenceADL","edumetroresidenceADL",
"canopyhillsEX","bsp21ADL","residensisasarsateriaADL","residensiberliansetapak2ADL","pelangidamansaraHF",
"montebayuADL","dsiniresidenceHF","armaniresidenceADL","suteraniaga8DPM","residensiamansuriAW",
"neusuitesSHU","dutasuriaresidency35storeysuperlinkterraceEX","ceriaresidenceMMN","neusuitesADL","metacityresidenceEX",
"mentaricourtADL","kelanaputericondominiumNS","halya2daunan2storeyterraceHF","savillekajangEX","pangsapuriindahriaMMN",
"kenangapointEX","edusphereatelierEX","alamimpian2storeyterraceHF","228kondominiumEX","ritmaperdanapuncakalamcornerlotHF",
"residensizamrudEX","pangsapuritunteja1MMN","gurneyheightsMAP","vistaharmoniresidenceEX","vistabangiNS",
"sunwaybatucavesEX","neusuitesEX","lestariperdana7NS","suasanalumayanADL","ritzeperdana1ADL",
"residensiadelia4LMZ","bandarbarubangi2storeyterraceSJH","acaciaresidencesLMZ","plazarahcondominiumMAP","iresidencePYH",
"bandardamaiperdana2storeyterraceMAP","prestigeresidenceADL","lifestylesuitesttdisentralisLNS","lbsskylakeresidenceADL","gayabangsarEX",
"dvineresidenceADL","bandarbarubangiseksyen4tambahan2storeyterraceSJH","lilyapartmentEYP","casasuriacondominiumNLH","platinumsplendorresidensisemarakMAP",
"kitabayucybersouth2storeyterraceEX","hennaresidencethequartzMAP","bandarsaujanaputraclusterlinksemidMMN","ttdijalantunmohdfuadduagroundfloorshopMAP","trinitywellnessaMAP",
"tamangreenwood1storeyterraceADL","skylineklcondominiumMAP","residensiplatinumterataiADL","puncakalamfasa11storeyterraceMMN","isuiteicityADL",
"isohoicityADL","heritagecondominiumMAP","endahriacondominiumADL","astoriaampangEX","tamanputraperdanatownhouseMMN",
"nexuskajangstationNS","greenwoodserayaNS","bandarbukitraja15storeyterraceNS","residensiputrasuriaEXP","tamanbukitmahkota2storeyterraceEX",
"srialamcondoDPM","savillemelawatiresidenceEX","mesahillDPM","dorsettresidenceADL","desapalmaDPM",
"danaukotasuiteEX","acaciaresidencesNS","antahtowerEX","youcity3ADL","suriadamansaraHF",
"skymeridienFPR","tiarafaberADL","residensidahliaADL","paisleyservicedresidencesADL","continewcondominiumNS",
"youcityiiiADL","residensidutamasdahliaLRH","puncakhijauanNS","platinumsplendorresidensisemarakADL","ostiabangibusinessavenueLRH",
"metaresidenceLRH","lakeparkresidenceADL","impianaonthewaterfrontcondominiumLRH","ehsanresidenceNS","cerradoSJH",
"apartmentrubyNS","vistahijauanNS","acaciasemenyihapartmentNS","sriixoraapartmentNS","tiaraparkhomesNS",
"saujanaamanjalansaujanaaman2storeyterraceNS","palmgardenapartmentNS","dwiputraresidencesMMN","verdiecodominiumsDPM","tamanpantaisepangputrajalanrajaudang42storeyterraceNS",
"lakefronthomesHF","pangsapurikemuningamanMMN","tamanperindustrianpuchongutamajalanutama1115storeyfactoryNS","residensizamrudNS","kiambangapartmentNS",
"residensiemaskajang2MMN","hillparkjalanhillparkniagashoplotNS","suriajayaesofoMMN","sinarpuchongtechnologyparkNS","tamanperindustrianairhitamjalanpermata2ks915storeysemidfactoryNS",
"menaramenjalaraNS","bandarparklandsshoplotNS","seniresidencesunsuriajalansunsuria725storeyterraceMMN","alstoneatamansubangmasjalansubangmas3storeyterraceMMN","ndira16sierraMMN",
"harmonielmina1MMN","tamansritanjungjalansritanjungsinglestoreyterraceLMZ","bandarbukitrajajalanmakyonglandedHF","2storeyterracehouseMMN","bayuputeriapartmentMMN",
"doublestoreyterraceMMN","tulipresidencedenaialamMMN","kr7residencesMMN","suriamewahresidensiEXP","semidetachedhousemeruMMN",
"pendulinecornerendlotMMN","pangsapuriindahmasEXP","pandanheightscondominiumEXP","kenangapointcondominiumEXP","doublestoreyterracetamandatoharunEXP",
"bayviewcourtapartmentsMMN","symphonyheightsADL","puriaiyuMMN2","pangsapuriserinilamEXP","idamanbukitjelutongMMN",
"bayuresidensiADL","tamancherasintanADL","thehamsteadADL","dpinesampangADL","ayumansuitesADL",
"hattasquareapartmentADL","kondorakyatEX","residensijalilmasEX","residensitasikmasADL","marisaADL",
"selesairesortEX","hatasquareEX","pusatkomersialseksyen7MMN","tamansamuderaADL","kristalviewMMN",
"ppamsetapakrivieraEX","petalingindahcondominiumADL","tamanserigombakEXP","srisentosaac4blockeMMN","sririaapartmentEX",
"apartmenttamantenagaNS","dpinesampangEX","floradamansaraADL","mainplaceresidenceADL","lejardincondominiumEXP",
"vistamillenniumcondominiumADL","bukitougcondominiumEX","prestigeresidencesADL","pangsapuririmba2MMN","vistaprimaMMN",
"bandarbarusentulapartmentEX","kristalviewMMN2","melurapartmentADL"
)

Write-Host "Total folders in list: $($Folders.Count)"
Write-Host ""

$Found = 0
$Missing = 0

foreach ($f in $Folders) {
    $path = Join-Path $BaseDir $f
    if (Test-Path $path) {
        $Found++
        if ($Force) {
            Remove-Item -Path $path -Recurse -Force
            Write-Host "DELETED: $path" -ForegroundColor Green
        } else {
            Write-Host "[dry-run] would delete: $path"
        }
    } else {
        $Missing++
        Write-Host "[not found, skipping]: $path" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Summary: $Found folders found, $Missing not found."
if (-not $Force) {
    Write-Host ""
    Write-Host "This was a DRY RUN. Nothing was deleted." -ForegroundColor Yellow
    Write-Host "Review the list above, then re-run with -Force to actually delete:"
    Write-Host "  .\delete_unitpic_folders.ps1 -Force"
}