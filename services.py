from koneksi import db_query
from datetime import datetime, timedelta

def get_last_so_date():
    q = """
        SELECT so.TANGGAL
        FROM inventory.stok_opname so
        GROUP BY so.TANGGAL
        ORDER BY so.TANGGAL DESC
        LIMIT 1
    """
    rows = db_query(q)
    if not rows:
        return None

    ts = rows[0]["TANGGAL"]
    return ts.strftime("%Y-%m-%d")

def get_ruangan_list():
    sql = """
        SELECT r.ID, r.DESKRIPSI
        FROM master.ruangan r
        WHERE r.ID LIKE '10304%%'
          AND r.JENIS = 5
        ORDER BY r.DESKRIPSI;
    """
    return db_query(sql)

def get_master_rows(kode_ruangan):
    q = """
    SELECT 
      br.ID AS ID_BARANG_RUANGAN,
      r.ID AS KODE_RUANGAN,
      r.DESKRIPSI AS RUANGAN,
      ib.ID AS ID_BARANG,
      ib.NAMA AS NAMA,
      sat.NAMA AS SATUAN,
      kat.NAMA AS KATEGORI,
      hb.HARGA_JUAL,
      tsr.STOK,
      br.`STATUS` AS STATUS_BARANG_RUANGAN,
      ib.`STATUS` AS STATUS_BARANG,
      tsr.TANGGAL
    FROM inventory.barang_ruangan br 
    LEFT JOIN inventory.transaksi_stok_ruangan tsr ON tsr.BARANG_RUANGAN = br.ID
    LEFT JOIN master.ruangan r ON r.ID = br.RUANGAN
    LEFT JOIN inventory.barang ib ON ib.ID = br.BARANG
    LEFT JOIN inventory.satuan sat ON sat.ID = ib.SATUAN
    LEFT JOIN inventory.kategori kat ON kat.ID = ib.KATEGORI
    LEFT JOIN inventory.harga_barang hb ON hb.BARANG = ib.ID AND hb.`STATUS` = 1
    WHERE br.RUANGAN = %s
    GROUP BY ib.ID
    ORDER BY tsr.TANGGAL DESC;
    """
    return db_query(q, (kode_ruangan,))

def get_stok_rows_pre(cutoff_date, kode_ruangan):
    cutoff_ts = cutoff_date + " 23:59:59"
    q = """
    SELECT 
        br.ID ID_BARANG_RUANGAN,
        r.ID KODE_RUANGAN,
        r.DESKRIPSI RUANGAN,
        ib.ID ID_BARANG,
        ib.NAMA NAMA,
        sat.NAMA SATUAN,
        kat.NAMA KATEGORI,
        hb.HARGA_JUAL,

        IFNULL((
            SELECT t.STOK
            FROM inventory.transaksi_stok_ruangan t
            WHERE t.BARANG_RUANGAN = br.ID
              AND t.TANGGAL < %s
            ORDER BY t.TANGGAL DESC, t.ID DESC
            LIMIT 1
        ), 0) STOK,

        br.`STATUS` STATUS_BARANG_RUANGAN,
        ib.`STATUS` STATUS_BARANG,

        IFNULL((
            SELECT t.TANGGAL
            FROM inventory.transaksi_stok_ruangan t
            WHERE t.BARANG_RUANGAN = br.ID
              AND t.TANGGAL < %s
            ORDER BY t.TANGGAL DESC, t.ID DESC
            LIMIT 1
        ), '0000-00-00 00:00:00') TANGGAL

    FROM inventory.barang_ruangan br
    JOIN master.ruangan r ON r.ID = br.RUANGAN
    JOIN inventory.barang ib ON ib.ID = br.BARANG
    LEFT JOIN inventory.satuan sat ON sat.ID = ib.SATUAN
    LEFT JOIN inventory.kategori kat ON kat.ID = ib.KATEGORI
    LEFT JOIN inventory.harga_barang hb ON hb.BARANG = ib.ID AND hb.`STATUS` = 1
    WHERE br.RUANGAN = %s
    GROUP BY ib.ID
    ORDER BY TANGGAL DESC;
    """
    return db_query(q, (cutoff_ts, cutoff_ts, kode_ruangan))

def _get_so_final_header(cutoff_date, kode_ruangan):
    start_ts = cutoff_date + " 00:00:00"

    dt_cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d")
    next_day = dt_cutoff + timedelta(days=1)
    end_ts = next_day.strftime("%Y-%m-%d") + " 05:59:59"

    q_header = """
        SELECT so.ID, so.TANGGAL
        FROM inventory.stok_opname so
        WHERE so.RUANGAN = %s
          AND so.STATUS = 'Final'
          AND so.TANGGAL BETWEEN %s AND %s
        ORDER BY so.TANGGAL DESC
        LIMIT 1
    """
    rows = db_query(q_header, (kode_ruangan, start_ts, end_ts))
    if not rows:
        return None
    return rows[0]

def get_so_final_rows(cutoff_date, kode_ruangan):
    header = _get_so_final_header(cutoff_date, kode_ruangan)
    if not header:
        return []

    so_id = header["ID"]
    so_tanggal = header["TANGGAL"]

    q_detail = """
        SELECT
            sod.ID IDSO,
            sod.STOK_OPNAME, 
            sod.BARANG_RUANGAN,
            b.ID ID_BARANG,
            b.NAMA NAMA_BARANG,
            sod.MANUAL STOK_POST_SO,
            hb.HARGA_JUAL,
            r.ID KODE_RUANGAN,
            r.DESKRIPSI RUANGAN,
            %s TANGGAL_POST_SO
        FROM inventory.stok_opname_detil sod
        JOIN inventory.stok_opname so ON sod.STOK_OPNAME=so.ID
        JOIN inventory.barang_ruangan br ON br.ID = sod.BARANG_RUANGAN
        JOIN inventory.barang b ON b.ID = br.BARANG
        JOIN inventory.harga_barang hb ON hb.BARANG = b.ID AND hb.`STATUS` = 1
        JOIN master.ruangan r ON r.ID=so.RUANGAN
        WHERE sod.STOK_OPNAME = %s
    """
    detail_rows = db_query(q_detail, (so_tanggal, so_id))
    return detail_rows
