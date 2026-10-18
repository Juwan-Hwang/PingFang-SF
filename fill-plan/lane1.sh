python3 scan2.py https://dumps.wikimedia.org/zh_yuewiki/latest/zh_yuewiki-latest-pages-articles-multistream.xml.bz2 0 71000000 data/d_yue0.pkl
python3 scan2.py https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles-multistream.xml.bz2 0 200000000 data/d_zh0.pkl
python3 scan2.py https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles-multistream.xml.bz2 900000000 1100000000 data/d_zh2.pkl
python3 scan2.py https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles-multistream.xml.bz2 1800000000 2000000000 data/d_zh4.pkl
python3 scan2.py https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles-multistream.xml.bz2 2700000000 2900000000 data/d_zh6.pkl
python3 scan2.py https://dumps.wikimedia.org/kowiki/latest/kowiki-latest-pages-articles-multistream.xml.bz2 0 200000000 data/d_ko0.pkl
python3 scan2.py https://dumps.wikimedia.org/kowiki/latest/kowiki-latest-pages-articles-multistream.xml.bz2 700000000 900000000 data/d_ko2.pkl
python3 scan2.py https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2 3000000000 3200000000 data/d_en0.pkl
echo done > data/lane1.done
