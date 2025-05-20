-- Compatible with msAccess and BRSIS spaceQRY, change the adm name to get the table (you need the srsxxx.mdb files)
SELECT  DISTINCT
    com_el.ntc_id,
    com_el.tgt_ntc_id,
    com_el.adm,
    com_el.ntwk_org,
    com_el.sat_name,
    com_el.long_nom,
    com_el.prov,
    com_el.d_rcv,
    com_el.st_cur,

    orbit.orb_id,
    orbit.nbr_sat_pl,
    orbit.apog_km,
    orbit.perig_km,
    orbit.op_ht_km,

    s_beam.emi_rcp,
    s_beam.beam_name,

    grp.grp_id,
    grp.freq_min,
    grp.freq_max,
    grp.bdwdth,
    grp.d_inuse,
    grp.d_reg_limit,
    grp.d_prot_eff,
    grp.f_biu,

    emiss.seq_no,
    emiss.pwr_ds_max,
    emiss.design_emi,

    carrier_fr.freq_carr,
    carrier_fr.seq_emiss,
    carrier_fr.seq_no

FROM
    (
        (
            (
                (
                    (
                        SELECT * FROM com_el
                        WHERE adm = 'D'
                          AND (
                                (ntc_type IN ('G', 'N') AND ntf_rsn IN ('A', 'C', 'N', 'U', 'D'))
                                OR (ntf_rsn = 'C' AND ntc_type IN ('S', 'T'))
                              )
                    ) AS com_el
                    LEFT JOIN orbit ON com_el.ntc_id = orbit.ntc_id
                )
                LEFT JOIN s_beam ON com_el.ntc_id = s_beam.ntc_id
            )
            LEFT JOIN (
                SELECT * FROM grp
                WHERE
                    (freq_max > 401.825 AND freq_min < 402)
                    OR (freq_max > 2055 AND freq_min < 2075)
                    OR (freq_max > 2202 AND freq_min < 2239)
            ) AS grp ON s_beam.ntc_id = grp.ntc_id AND s_beam.beam_name = grp.beam_name AND s_beam.emi_rcp = grp.emi_rcp
        )
        LEFT JOIN emiss ON grp.grp_id = emiss.grp_id
    )
    LEFT JOIN carrier_fr ON emiss.grp_id = carrier_fr.grp_id AND emiss.seq_no = carrier_fr.seq_emiss
WHERE
                    (grp.freq_max > 401.825 AND grp.freq_min < 402)
                    OR (grp.freq_max > 2055 AND grp.freq_min < 2075)
                    OR (grp.freq_max > 2202 AND grp.freq_min < 2239);