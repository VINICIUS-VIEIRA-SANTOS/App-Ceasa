import 'package:flutter/material.dart';
import '../api/api_service.dart';

class VendasPage extends StatefulWidget {
  const VendasPage({super.key});

  @override
  State<VendasPage> createState() => _VendasPageState();
}

class _VendasPageState extends State<VendasPage> {
  final ApiService api = ApiService();
  List vendas = [];
  bool carregando = true;

  @override
  void initState() {
    super.initState();
    carregarVendas();
  }

  void carregarVendas() async {
    final dados = await api.getVendas();
    setState(() {
      vendas = dados;
      carregando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Vendas')),
      body: carregando
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: vendas.length,
              itemBuilder: (context, index) {
                final v = vendas[index];
                return ListTile(
                  title: Text("Venda #${v['id']}"),
                  subtitle: Text("Forma de pagamento: ${v['forma_pagamento']}"),
                  trailing: Text("R\$ ${v['valor_total']}"),
                );
              },
            ),
    );
  }
}
